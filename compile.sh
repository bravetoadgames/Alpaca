rm -r dist
pyinstaller --onefile alpaca.py
staticx dist/alpaca dist/alpaca_static
rm alpaca
mv dist/alpaca_static ./alpaca
tar -czf alpaca-1.0.1-ubuntu-x86_64.tar.gz alpaca readme.txt identities.json

