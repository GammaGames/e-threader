# e-threader

Send reddit threads to a kindle via a discord bot

### How to use

1. Copy `.env.example` and fill in your own settings
2. Create empty sqlite file with `touch db.sqlite`
3. Start with `docker-compose up --build`
4. React to "🙋" message in discord server
5. Set up account
6. DM bot to send books to kindle

### Commands

- `?email [EMAIL]`: Set user email
- `[LINK]`: Send reddit thread to your email as an e-book (default command)
- `?thread [LINK]`: Send reddit thread to your email as an e-book
- `?collect [LINK]`: Send links from reddit thread/wiki to your email as an e-book
- `?help`: Print help text

God help you if you try to look into this code, it's held together with duct-tape and dreams. 
