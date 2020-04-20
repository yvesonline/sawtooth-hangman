Containers:
- `hangman-tp-py`: Hangman Transaction Processor in Python
- `hangman-client-py`: Hangman Client in Python
- `hangman-web-py`: Hangman Web Frontend in Python

State:
- `Game`
 - `name`
 - `word`
 - `misses`
 - `host`
 - `guesser`

Payload:
- `name,action,guess`

Actions:
- `create`
- `delete`
- `guess`