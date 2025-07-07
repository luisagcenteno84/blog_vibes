import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Post, Tag

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seeds the database with sample data."""
    # Find the first user to be the author
    user = User.query.first()

    if user:
        # Clear existing posts for this user to avoid duplicates
        Post.query.filter_by(author=user).delete()
        # Clear all tags to ensure fresh seeding
        Tag.query.delete()
        db.session.commit() # Commit deletions before adding new data

        # Create fake posts
        post1 = Post(
            title='My Journey with Python',
            body='This is a post about my exciting journey learning the Python programming language. It has been a rewarding experience filled with challenges and triumphs.',
            author=user,
            thumbnail='https://placehold.co/600x400/20c997/FFFFFF/png?text=Python',
            status='published'
        )
        post2 = Post(
            title='Exploring the Cloud',
            body='I have been diving deep into cloud computing concepts, particularly with Google Cloud Platform. Deploying applications has never been easier.',
            author=user,
            thumbnail='https://placehold.co/600x400/20c997/FFFFFF/png?text=Cloud',
            status='published'
        )
        post3 = Post(
            title='A Guide to Web Design',
            body='In this post, I share some fundamental principles of modern web design, from color theory to responsive layouts. Good design is about communication.',
            author=user,
            thumbnail='https://placehold.co/600x400/20c997/FFFFFF/png?text=Design',
            status='draft' # This one is a draft
        )
        post4 = Post(
            title='Another Draft Post',
            body='This is another post that is currently in draft status and should only be visible to the author.',
            author=user,
            thumbnail='https://placehold.co/600x400/20c997/FFFFFF/png?text=Draft',
            status='draft'
        )

        # Add tags
        tag1 = Tag(name='Python')
        tag2 = Tag(name='Programming')
        tag3 = Tag(name='Cloud')
        tag4 = Tag(name='GCP')
        tag5 = Tag(name='Web Design')
        tag6 = Tag(name='Drafts')

        post1.tags.append(tag1)
        post1.tags.append(tag2)
        post2.tags.append(tag3)
        post2.tags.append(tag4)
        post3.tags.append(tag5)
        post3.tags.append(tag6) # Add a tag to the draft post
        post4.tags.append(tag6)

        db.session.add_all([post1, post2, post3, post4, tag1, tag2, tag3, tag4, tag5, tag6])
        db.session.commit()
        print('Database seeded with sample posts and tags.')
    else:
        print('No user found in the database. Please create a user first.')

def init_app(app):
    app.cli.add_command(seed_db_command)
