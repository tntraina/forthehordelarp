from flask import Flask, jsonify, render_template, request, redirect, url_for
import sqlite3
from flask import g

app = Flask(__name__)

CHARACTERS = []

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('.\\game_db.sqlite')
        g.db.row_factory = sqlite3.Row 
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    cur = get_db().cursor()
    if request.method == 'POST':
        # Create a dictionary of all characters, setting True if checked, False otherwise
        # Note: HTML checkboxes only send a value if they are checked.
        updated_data = request.form.getlist('character_ids')  # Get list of checked character IDs
        print(len(updated_data))
        print(updated_data)
        for d in updated_data:
            str_id = d.split("_")[1]  # Extract the ID from the value (e.g., "picked_1" -> "1")
            target_sql = f'UPDATE basic_data SET chosen=1 WHERE id={str_id}'
            target_entry = cur.execute(target_sql)
        cur.connection.commit()
        return redirect(url_for('admin'))

    elif request.method == 'GET':
        data = cur.execute('SELECT * FROM basic_data bd WHERE id IN (SELECT id FROM basic_data bd WHERE bd.id % 100 = 1 UNION SELECT id FROM basic_data bd WHERE bd.chosen = 1 UNION SELECT possible_dest FROM choice_paths cp WHERE origin in (SELECT id FROM basic_data bd WHERE bd.chosen = 1))')        
        return render_template('admin.html', characters=data.fetchall())


@app.route('/character/<charid>')
def character(charid):
    cur = get_db().cursor()
    data = cur.execute('SELECT id FROM basic_data WHERE chosen = 1')
    nodelist = [row['id'] for row in data.fetchall()]
    print(nodelist)

    filename = f'character_{charid}.html'

    return render_template(filename, game_events=nodelist)


@app.route('/game_stats')
def constats():
    conn = get_db()
    stats = conn.execute('SELECT * FROM game_stats').fetchall()
    return render_template('game_stats.html', stats=stats)


@app.route('/reset')
def reset():
    cur = get_db().cursor()
    cur.execute('UPDATE basic_data SET chosen=0')
    cur.connection.commit()
    cur.execute('UPDATE game_stats SET current_value = default_value')
    cur.connection.commit()
    return redirect(url_for('admin'))

# Route to get all characters from the database
@app.route('/character/all', methods=['GET'])
def get_all_characters():
    conn = get_db()
    characters = conn.execute('SELECT * FROM characters').fetchall()
    conn.close()
    return render_template('characters.html', characters=jsonify([dict(character) for character in characters]))

@app.route('/queue')
def get_character_queue():
    cur = get_db().cursor()
    upcoming_data = cur.execute('SELECT possible_dest FROM choice_paths cp WHERE cp.possible_dest NOT IN (SELECT id FROM basic_data bd WHERE bd.chosen = 1) AND cp.origin IN (SELECT id FROM basic_data bd WHERE bd.chosen = 1)').fetchall()
    return render_template('npc_queue.html', stats=upcoming_data)


if __name__ == '__main__':
    app.run(debug=True)