"""Add unique constraint to passphrase

Revision ID: bde5c44da863
Revises: 7e8a02b156df
Create Date: 2020-03-14 20:08:39.397055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bde5c44da863'
down_revision = '7e8a02b156df'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('passphrase_uc', 'users', ['passphrase'])
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('passphrase_uc', 'users', type_='unique')
    # ### end Alembic commands ###
