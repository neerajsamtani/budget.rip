# Budget

A simple personal budgeting app.

## Features

### Connected Accounts
- View all connected financial accounts (Stripe, Venmo, Splitwise)
- Refresh individual accounts without refreshing all data
- Real-time balance and status information
- Reactivate inactive accounts

## Setting up the client

1. Configure `server/.env` using `server/.env.example`, including PostgreSQL and Stripe credentials.

2. Install and run the shared backend from the repository root:

~~~
cd server
uv sync
uv run alembic upgrade head
uv run python application.py
~~~

3. In another terminal, install and run the client from the repository root:

~~~
cd client
npm install
npm start
~~~

4. Open [http://dev.localhost:5173/](http://dev.localhost:5173/).

Stripe API configuration is shared by the backend in `server/clients.py`, using
the single `STRIPE_API_VERSION` constant in `server/constants.py`.

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
