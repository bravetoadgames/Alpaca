rm -r dist
rm alpaca
pyinstaller --onefile alpaca.py
staticx dist/alpaca dist/alpaca_static
mv dist/alpaca_static ./alpaca
tar -czf alpaca-1.2.8-ubuntu-x86_64.tar.gz alpaca readme.txt identities.json

