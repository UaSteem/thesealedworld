// Opt-in only: run in an authenticated administrative mongosh session.
// Creates a NEW database-scoped user; never rotates or modifies existing users.
(() => {
  if (process.env.MONGO_PROVISION_CONFIRM !== "create-database-user") {
    throw new Error("Explicit MONGO_PROVISION_CONFIRM=create-database-user is required");
  }
  const database = process.env.MONGO_PROVISION_DATABASE;
  const username = process.env.MONGO_PROVISION_USERNAME;
  const password = process.env.MONGO_PROVISION_PASSWORD;
  if (!database || !/^[A-Za-z][A-Za-z0-9_-]{0,62}$/.test(database) ||
      ["admin", "config", "local"].includes(database)) {
    throw new Error("An explicit application database is required");
  }
  if (!username || !/^[A-Za-z][A-Za-z0-9_-]{0,62}$/.test(username) ||
      ["root", "admin", "mongodb"].includes(username)) {
    throw new Error("A distinct application username is required");
  }
  if (!password || password.length < 24) {
    throw new Error("A new application password of at least 24 characters is required");
  }
  const target = db.getSiblingDB(database);
  if (target.getUser(username) !== null) {
    throw new Error("Application user already exists; explicit rotation requires a separate operation");
  }
  target.createUser({user: username, pwd: password, roles: [{role: "readWrite", db: database}]});
  print("Application database user created; default deployment credentials were not changed");
})();
