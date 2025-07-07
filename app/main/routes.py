from flask import render_template, abort, flash, redirect, url_for, request, current_app, session
from flask_login import login_required, current_user
from app.main import bp
from app.models import Post, Tag
from app.forms import PostForm, ChatForm, SearchForm
import google.generativeai as genai
from app import db
from sqlalchemy import or_

@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(status='published').order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('main/index.html', title='Home', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=current_user).order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.dashboard', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.dashboard', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('main/dashboard.html', title='Dashboard', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/posts/<int:post_id>', methods=['GET'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    # If post is a draft and current user is not the author, abort
    if post.status == 'draft' and (not current_user.is_authenticated or post.author != current_user):
        abort(403) # Forbidden

    return render_template('main/post.html', title=post.title, post=post)

@bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data,
                    thumbnail=form.thumbnail.data, status=form.status.data,
                    author=current_user)
        
        # Handle tags
        tag_names = [t.strip() for t in (form.tags.data or '').split(',') if t.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            post.tags.append(tag)

        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('main/create_post.html', title='Create New Post', form=form)

@bp.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403) # Forbidden

    form = PostForm()
    chat_form = ChatForm()
    
    # Initialize chat history from session
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    display_history = session['chat_history']

    if form.validate_on_submit():
        flash(f"Attempting to save status: {form.status.data}", 'info')
        post.title = form.title.data
        post.body = form.body.data
        post.thumbnail = form.thumbnail.data
        post.status = form.status.data
        
        # Handle tags
        post.tags.clear()
        tag_names = [t.strip() for t in (form.tags.data or '').split(',') if t.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            post.tags.append(tag)

        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    elif chat_form.validate_on_submit():
        user_message = chat_form.message.data
        
        genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Use session history for the chat
        chat_session = model.start_chat(history=session['chat_history'])

        try:
            response = chat_session.send_message(user_message)
            model_response = response.text
            
            # Append to session history
            session['chat_history'].append({'role': 'user', 'parts': [user_message]})
            session['chat_history'].append({'role': 'model', 'parts': [model_response]})
            session.modified = True # Mark session as modified
            
            # Clear the chat form after submission
            chat_form.message.data = ''

            # Re-render the template instead of redirecting
            return render_template('main/edit_post.html', title='Edit Post', form=form, chat_form=chat_form, chat_history=display_history, post=post)
        except Exception as e:
            flash(f"Error communicating with Gemini: {e}", 'danger')
            current_app.logger.error(f"Gemini API Error: {e}")

    elif request.method == 'GET':
        form.title.data = post.title
        form.body.data = post.body
        form.thumbnail.data = post.thumbnail
        form.status.data = post.status
        form.tags.data = ", ".join([tag.name for tag in post.tags])

    return render_template('main/edit_post.html', title='Edit Post', form=form, chat_form=chat_form, chat_history=display_history, post=post)

@bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403) # Forbidden
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    posts = []
    query = ""
    if form.validate_on_submit():
        query = form.q.data
        posts = Post.query.filter(
            Post.status == 'published',
            or_(
                Post.title.ilike(f'%{query}%'),
                Post.body.ilike(f'%{query}%')
            )
        ).order_by(Post.timestamp.desc()).all()
    elif request.method == 'GET' and 'q' in request.args:
        query = request.args.get('q')
        form.q.data = query
        posts = Post.query.filter(
            Post.status == 'published',
            or_(
                Post.title.ilike(f'%{query}%'),
                Post.body.ilike(f'%{query}%')
            )
        ).order_by(Post.timestamp.desc()).all()

    return render_template('main/search_results.html', title='Search Results', posts=posts, query=query, form=form)

@bp.route('/tags/<tag_name>')
def posts_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter_by(name=tag_name).first_or_404()
    posts = Post.query.filter(
        Post.status == 'published',
        Post.tags.any(name=tag_name)
    ).order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('main.posts_by_tag', tag_name=tag_name, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.posts_by_tag', tag_name=tag_name, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('main/posts_by_tag.html', title=f'Posts tagged "{tag_name}" ', posts=posts.items, tag_name=tag_name,
                           next_url=next_url, prev_url=prev_url)