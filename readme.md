# **Colors of Bharat – Catalog App**

This project states the various cultural heritage of Bharat. It has catalog of different arts like Dance, Music, Martial Arts etc. which are further divided individual types.

The website has Login System in place which uses Google Open ID Connect to authenticate the identity of User after which the user can add a Category in catalog and further add items and only the user that has created the category has the access to delete it.

## **Getting Started**

The project is configured to run at localhost(0.0.0.0) port 8000.
 To run the project the project you need to run application.py in the catalog folder.

### **Prerequisites**

Pip, oauth2client, requests, python flask, httplib2, sqlalchemy, Google Account

sudo apt-get install python-pip

pip install --upgrade flask

pip install requests



### Features

·         The app has login system to authenticate users with their Google Account.

·         The users can view catalog without any login via (localhost:8000/catalog).

·         User can new categories and items , perform CRUD operation on categories they created.

·         Users cannot perform edit, delete operations on categories created by other users.

·         Users can add names, descriptions and photos (via url ) to a category/item.

·         Users have the ability to logout using Logout button in navigation bar present on each page.

·         To access the items in a category, user have to click on the image of the category.

·         To delete or edit, users have to click on the respective symbols of edit and delete on the image.

·         To read the description of an item, users have to click on the name of item.

 

 

### **API Endpoints**

API Endpoint for displaying all the categories

Localhost:8000/catalog.json

 

API Endpoint for displaying all the items in a category

Localhost:8000/catalog/<int:category_id>/item.json

 

API Endpoint for displaying all the information regarding a particular item

Localhost:8000/catalog.json



### **Public accessible URL without login****

To display the list of categories

Localhost:8000/catalog


 To display the list of items

Localhost:8000/catalog/<int:category:id>/items/

 

### **Built With**

- [*Flask*](http://flask.pocoo.org/)- Microframework for Python based on Werkzeug, Jinja 2
- [*SQLAlchemy*](https://www.sqlalchemy.org/) – Database 



## **Author**

- **Siddharth Pandey**

Created as a part of Udacity FullStack Web Developer II Program

 

## **License**

·         The logo of Colors of Bharat is created by me. The png of logo used is created by me. (Original Fonts utilized in making – Baron Neue, Ananda Namaste) 

 

·         The pictures used in the project to display categories and items are just for representation purposes. I do not hold any copyright over them.

The images are accessed via public domains and I do not in any way to be held responsible or liable for them and neither seek credit for them.

 