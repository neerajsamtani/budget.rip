# Budget

A simple personal budgeting app.

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
- Stripe connect new accounts so I can add BofA (Deadline Feb 6)
- Deploy Online

- Graphs
- All Page is diff from create events page
- Null out Payments? Do I need this
- On server start, loop through all events and ensure the line_items have the event_id attached
- Clean Up Categories Drop Down. Allow Multiple Categories, Exclude Categories
- backup mongo
sudo mongodump --db flask_db --out ~/backups/mongobackups/$(date +'%m-%d-%y')


5. Go to [http://localhost:3000/](http://localhost:3000/)