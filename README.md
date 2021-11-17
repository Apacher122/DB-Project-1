# DB-Project-1

1. PostgreSQL database account: mc5090

2. application url

3.
Implementation of proposal: From the original proposal, we implemented be able to browse products based on item type ("Shop by category" tab) or brand ("Shop by brand" tab). We also allowed users to create an account ("Register" tab accessible on the home page) and to log in (also on the home page). No password is required; we simply check that the input username is one that is in our database. Once logged in, the user can leave reviews on items, connect with other users (profile tab), message them (messages tab), and make text posts (home page). If logged in, on an item page, a user can add the item with a quantity to their cart. The user can also enter the "Cart" tab to see the contents of their cart and previous orders, which includes the items that were in each order. If the user clicks "order" they can order what is currently in their cart.

 Additional implementation: We added some functionality that allowed for more comprehensive interaction with the database and a more logical and completed web app.
 This includes: a profile tab that shows the user their input information, a settings tab that allows the user to add a new address and specify their birthday and
 size preference, a newsfeed on the home page that shows your posts and your friends' posts, being able to remove a review once you have posted it on item pages,
 and being able to add a new address on the checkout page.

Note: On each product page, we implemented "showing reviews with associated photos" by querying the include_photo relationship set and just showing the photo_ids with their associated products. We did not attach actual image files to those photo IDs like we did with other product photos on the site. We found that it did not make much sense since our review post formats are just a thumbs up or a thumbs down without text, so associating a real photo might look funny. There is no way to "attach a photo" when making a new review.

4.
Interesting web pages:
- Individual item pages (/item?=type[item name]&color=[color]): each page shows the product's information from the natural join of products and retailers (seller name, product name, product color if applicable, price, size, description). At the bottom of the page, we show the reviews from the table review_posts (reviewer name, thumbs up/down) and also show the average score of the item, i.e., the proportion of thumbs up to the total number of reviews
- 
