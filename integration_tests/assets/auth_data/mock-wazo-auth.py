import sys

from flask import Flask, jsonify

app = Flask(__name__)

port = int(sys.argv[1])

context = ('/etc/ssl/server.crt', '/etc/ssl/server.key')

tokens = {'valid-token': 'uuid',
          'new-valid-token': 'new_uuid'}


@app.route("/0.1/token", methods=['POST'])
def token_post():
    return jsonify({
        'data': {
            'auth_id': tokens['new-valid-token'],
            'token': 'new-valid-token',
        }
    })


@app.route("/0.1/token/<token>", methods=['GET'])
def token_get(token):
    if token not in tokens:
        return '', 404

    return jsonify({
        'data': {
            'auth_id': tokens[token],
            'token': token,
        }
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port, ssl_context=context, debug=True)