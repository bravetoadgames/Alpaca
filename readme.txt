+-------------------------------------------------------+
| Alpaca 1.0                                            |
| An Ollama identity crisis                             |
+-------------------------------------------------------+
| Written by Google Gemini, prompts by Arjen Schumacher |
| May 11, 2026                                          |
+-------------------------------------------------------+

Welcome to Alpaca, your lightweight Ollama companion. Create any identity you want
and start a conversation with it!

+------------------+
|- How to install -|
+------------------+
Just place these files in its own directory. It should be these files:

- alpaca.bin
- identities.json
- readme.txt (this file)


+--------------+
|- How to run -|
+--------------+
Be sure to have Ollama installed on your system. Also be sure you have pulled one or more models to your
local harddisk. If Ollama is installed, simply start alpaca.bin and start chatting!


+--------------------------------+
|- How to create a new identity -|
+--------------------------------+
Open the file identities.json with a text-editor like Geany or Nano.

Add a new line like this example:
	"Marco Polo - Explorer": "You are an explorer from centuries ago who traveled to the far east. You speak the old language.",

Keep in mind to end the line with a comma to not compromise the JSON file structure.
After you saved the JSON file to disk, just start alpaca.bin again. The identity should be available.



