1. Team members' UNIs: mc5090 and rda2126
2. PostgreSQL account: mc5090
3. Our three implemented additions are:
  - A new text attribute called "full_desc" for the PRODUCTS table. It stores a longer form text description of the product.
  - A new array attribute called "prev_addresses" to the LIVES_AT table. This array saves a list of addresses that the user has either previously lived at or has shipped an order to. The primary key (street_1, street_2, zip) remains to store each user's current residence and is the address that is set in our "settings" tab in our front-end implementation.
  - A new composite type called "friendship_type" which stores attributes "user_id" and "connection". We altered our original table "connected_to" to a table of "friendship_type" that keeps track which users are connected to which other users.
5. Example queries:
  - Get the name of every customer who has in their cart one or more items that are specfied as imported in their descriptions and the total number of such items (for example, if a user has in their cart two items that are imported with respective quantities 1 and 3, this query will output the user's name and count 4):
    SELECT U.name, SUM(C.quantity)
    FROM products P, has_in_cart C, users U
    WHERE P.product_number = C.product_number AND U.user_id = C.user_id AND full_desc @@ to_tsquery('imported')
    GROUP BY U.name;
  - Get the names of users with overlapping previous addresses
    SELECT U1.name, U2.name
    FROM users U1, users U2, lives_at L1, lives_at L2
    WHERE U1.user_id = L1.user_id AND U2.user_id = L2.user_id AND L1.user_id != L2.user_id AND L1.prev_addresses && L2.prev_addresses;
  - Get users who are connected to a user who lives at an addresses with ZIP code 12345
    SELECT U1.name, U2.name
    FROM users U1, users U2, lives_at L, connected_to C
    WHERE U1.user_id = C.user_id AND U2.user_id = C.connection AND U2.user_id = L.user_id AND L.zip = '12345'; 
