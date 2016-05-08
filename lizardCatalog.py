from pkg import app
app.secret_key = 'super_secret_key'
app.debug = True
app.run(host='0.0.0.0', port=8000)
