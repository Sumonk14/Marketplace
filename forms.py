from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf.file import FileField, FileAllowed # <-- NEW IMPORTS for file uploads


# The form for adding a new item/article
class ArticleForm(FlaskForm):
    # Existing Fields
    title = StringField('Item Title', [
        Length(min=1, max=200),
        DataRequired()
    ])
    
    # --- New Marketplace Fields ---
    
    price = DecimalField('Price ($)', validators=[
        DataRequired(message="Please enter a price."), 
        NumberRange(min=0.01, message="Price must be greater than zero.")
    ])
    
    details = TextAreaField('Item Details/Description', [
        Length(min=10, message="Description must be at least 10 characters long."),
        DataRequired()
    ])
    
    contact_info = StringField('Contact Info (Phone or Email)', [
        Length(min=5, max=100), 
        DataRequired(message="Please provide contact information.")
    ])
    
    # Image Upload Field
    image = FileField('Item Image (PNG, JPG, GIF)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!'), # Validate file extension
        DataRequired(message="An image is required.")
    ])


class EditArticleForm(FlaskForm):
    # Keep all other fields the same, with DataRequired
    title = StringField('Item Title', [
        Length(min=1, max=200),
        DataRequired()
    ])
    
    price = DecimalField('Price ($)', validators=[
        DataRequired(message="Please enter a price."), 
        NumberRange(min=0.01, message="Price must be greater than zero.")
    ])
    
    details = TextAreaField('Item Details/Description', [
        Length(min=10, message="Description must be at least 10 characters long."),
        DataRequired()
    ])
    
    contact_info = StringField('Contact Info (Phone or Email)', [
        Length(min=5, max=100), 
        DataRequired(message="Please provide contact information.")
    ])
    
    # CRITICAL CHANGE: Use Optional() instead of DataRequired()
    image = FileField('Replace Item Image (Optional)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!'),
        Optional() 
    ])