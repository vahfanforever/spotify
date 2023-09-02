from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def callback():
    code = request.args.get('code')
    return code

if __name__ == '__main__':
    app.run()
