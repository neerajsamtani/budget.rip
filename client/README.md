# Budget

A simple personal budgeting app.

## Features

### Connected Accounts
- View all connected financial accounts (Stripe, Venmo, Splitwise)
- Refresh individual accounts without refreshing all data
- Real-time balance and status information
- Reactivate inactive accounts

## Setting up the client

1. Build the server

~~~
pip3 install -r requirements.txt
~~~

2. Run the server

~~~
export FLASK_APP=server.py
python3 -m flask run --port=4242
~~~

3. Build the client app

~~~
npm install
~~~

4. Run the client app

~~~
npm start
~~~

TODO:
- Deploy Online
- Fix Leaky Abstraction of DB Filters
- Move CRUD endpoints into spearate folder
- Optimize Refresh Logic
- Add OAuth Login
- Move Payment Method from Stripe to which Bank Account
- Single Events: Hints for Name and Category (from Hints.json or current name in Camel Case)
- Transfer between Accounts auto suggested, N/A category (two transactions sum 0)
- Search Line Items and Events

- All Page is diff from create events page
- Null out Payments? Do I need this
- On server start, loop through all events and ensure the line_items have the event_id attached
- Clean Up Categories Drop Down. Allow Multiple Categories, Exclude Categories
- backup mongo
sudo mongodump --uri <uri> --db flask_db --out ~/backups/mongobackups/$(date +'%m-%d-%y')

LOGIN
- Get current user and ensure that all data belongs to current user
    - Need to migrate all data to have user id
    - Automatically get user Implementation in server/resources/event.py and implemented in user_lookup_callback
- Ensure CSRF Protection in server/application.py
    - Cookie should have samesite and httponly
- Frontend should have a context provider that provides info for the current user

5. Go to [http://localhost:3000/](http://localhost:3000/)