# First hour back — getting the app running

Do these in order. Nothing here needs code written; it's account setup, two SQL files, and one run configuration.
Message me at any step that doesn't behave and we'll work through it together.

## 1. Create the database (10 minutes)

1. Go to https://neon.tech and sign up. The free tier is enough for this project.
2. Create a project. Name it `festimize`. Take the default Postgres version, and pick the region closest to you.
3. Neon creates a database called `neondb` automatically. That's fine — no need to make another.

## 2. Create the tables (5 minutes)

1. In the Neon dashboard, open **SQL Editor** in the left sidebar.
2. Open `db/schema.sql` from this folder, select all, copy, paste into the editor, press **Run**.
3. Check it worked — run this in the same editor:

   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public' ORDER BY table_name;
   ```

   You should see 13 tables, starting with `app_user`, `artist_momentum`, `artist_score`, `artist_tag`.

If it errors partway through, the whole thing rolled back (the file is wrapped in a transaction), so nothing is half-created. Send me the error.

## 3. Load the demo festivals (5 minutes)

1. Same editor: copy in `db/seed_demo.sql`, press **Run**.
2. Check it:

   ```sql
   SELECT (SELECT count(*) FROM dim_artist)       AS artists,
          (SELECT count(*) FROM artist_tag)       AS tags,
          (SELECT count(*) FROM fact_performance) AS performances;
   ```

   Expect roughly 67 artists, around 470 tags, and 70 performances.

3. Have a look at what you just loaded:

   ```sql
   SELECT s.name AS stage, a.name AS artist, p.starts_at, p.ends_at
   FROM fact_performance p
   JOIN dim_artist a ON a.artist_id = p.artist_id
   JOIN dim_stage  s ON s.stage_id  = p.stage_id
   ORDER BY p.starts_at
   LIMIT 20;
   ```

   That's your Bloodstock 2027 Friday. It is fabricated demo data — real artists, invented lineup.

## 4. Get the connection details (5 minutes)

In the Neon dashboard, find **Connection Details**. You need three things:

- the host, something like `ep-cool-name-123456.us-east-2.aws.neon.tech`
- the database name, `neondb`
- the user and password

The JDBC URL the app wants looks like:

```
jdbc:postgresql://<host>/neondb?sslmode=require
```

**Do not paste the password into any file inside this folder.** It would end up in git. Step 5 keeps it out.

## 5. Run the app (15 minutes, most of it downloads)

1. IntelliJ → **File → Open** → select `app/pom.xml` → **Open as Project**. First import downloads Maven and the dependencies; give it a few minutes.
2. If it asks for an SDK, pick your installed JDK (you have 26; the project targets 21, which is fine).
3. Open `FestimizeApplication` (in `src/main/java/com/festimize`), click the green arrow once so a run configuration exists, and let it fail.
4. **Run → Edit Configurations**, select that configuration, and add three environment variables:

   ```
   DATABASE_URL=jdbc:postgresql://<your-host>/neondb?sslmode=require
   DB_USER=<your-user>
   DB_PASSWORD=<your-password>
   ```

5. Run it again. Watch for `Started FestimizeApplication` in the console.
6. Open http://localhost:8080/register, create an account, and sign in. Then visit http://localhost:8080/lineup.

## What "working" looks like at the end of this

The app boots, you can register and log in, and the pages render as skeletons. They will **not** show real festival data yet — wiring the pages to the database is the first coding task, not part of setup.

## If something breaks

| What you see | What it means |
|---|---|
| `Schema-validation: missing table` | `schema.sql` didn't fully apply. Re-run step 2 and read the error it gives. |
| `FATAL: password authentication failed` | Wrong user or password in the run configuration. |
| `The connection attempt failed` / hangs | Host is wrong, or `?sslmode=require` is missing from the URL. |
| `Web server failed to start. Port 8080 was already in use` | Something else is on 8080. Add `SERVER_PORT=8081` to the environment variables. |
| Maven import fails in IntelliJ | Check the SDK is set. If it still fails, run `./mvnw -v` in `app/` from the terminal and send me the output. |

## Then what

Once this is running, the build order is: wire the lineup page to the database, then the taste matching, then the scheduler. That's the work that has to be yours.
