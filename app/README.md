# Festimize — web application

Spring Boot 3.5 / Java 21 / Thymeleaf / Spring Data JPA / PostgreSQL.

This is a **skeleton**. It has the build, the database mapping, security and empty pages.
There is no scoring, no ranking and no scheduling — every page renders static placeholder
content and says so on screen.

## Before you run it: apply the schema

`db/schema.sql` owns the database. Hibernate is configured with `ddl-auto: validate`, so it
will refuse to start against a database that does not already match. Apply the schema first:

```sh
psql "$DATABASE_URL_PSQL" -f ../db/schema.sql
```

(`$DATABASE_URL_PSQL` being the `postgresql://user:pass@host/db` form that `psql` wants —
the app itself needs the JDBC form below.)

## Environment variables

| Variable       | Default                                        | Notes                          |
| -------------- | ---------------------------------------------- | ------------------------------ |
| `DATABASE_URL` | `jdbc:postgresql://localhost:5432/festimize`   | JDBC URL, not the `psql` URL   |
| `DB_USER`      | `festimize`                                    |                                |
| `DB_PASSWORD`  | `festimize`                                    |                                |
| `PORT`         | `8080`                                         |                                |

For Neon, remember `?sslmode=require` on the JDBC URL.

## Running

Maven is not installed; use the wrapper. It is the script-only wrapper, so there is no
`maven-wrapper.jar` in the repo — the first run downloads Maven itself into `~/.m2/wrapper`.

```sh
export DATABASE_URL='jdbc:postgresql://localhost:5432/festimize'
export DB_USER='festimize'
export DB_PASSWORD='...'

./mvnw spring-boot:run          # macOS / Linux
mvnw.cmd spring-boot:run        # Windows
```

Then open <http://localhost:8080/> — it redirects to `/setup`, which requires an account,
so you land on `/login`. Use **Create one** to register, then sign in.

### IntelliJ IDEA

Open the `app/` folder (the one with `pom.xml`) as the project; IDEA imports it as a Maven
project and picks up the wrapper. Set the three environment variables on the
`FestimizeApplication` run configuration. JDK 26 is fine as the project SDK — the build
targets release 21.

## Layout

```
src/main/java/com/festimize/
  domain/     JPA entities, one per table in db/schema.sql
  repo/       Spring Data repositories
  security/   form login, BCrypt, UserDetailsService over app_user
  web/        controllers (skeletons)
src/main/resources/
  application.yml
  templates/  layout.html fragment + setup / lineup / schedule / login / register
  static/css/festimize.css
```

Pages: `/setup`, `/lineup`, `/schedule` (all require sign-in); `/login` and `/register` are open.

## Notes on the mapping

- Entity names are Java-side: `Artist` is `dim_artist`, `Festival` is `dim_festival`,
  `FestivalEdition` is `dim_festival_edition`, `Stage` is `dim_stage`,
  `Performance` is `fact_performance`.
- `dim_date` has no entity — it is analytics-only, so `Performance.dateId` is a plain
  `Integer` rather than an association.
- `plan_item.item_type` is a `String` with `SET` / `REST` / `MEAL` constants on `PlanItem`,
  matching the database `CHECK`. Swap it for an enum if you prefer.
- `country` is `char(2)`, which Postgres reports as `CHAR`; the entities say so explicitly
  with `@JdbcTypeCode(SqlTypes.CHAR)` so `validate` does not trip over it.
