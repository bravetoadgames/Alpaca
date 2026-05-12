python3 -m nuitka --follow-imports --onefile alpaca.py
rm alpaca
mv alpaca.bin alpaca
tar -czf alpaca-1.0.1-ubuntu-x86_64.tar.gz alpaca readme.txt identities.json

