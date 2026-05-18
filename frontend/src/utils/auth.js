export const auth = {
  // REGISTER
  register(email, password, name) {
    const users = JSON.parse(localStorage.getItem("ams_users") || "[]");

    const cleanEmail = email.trim().toLowerCase();

    const exists = users.find(
      u => u.email.toLowerCase() === cleanEmail
    );

    if (exists) return null;

    const newUser = {
      name: name.trim(),
      email: cleanEmail,
      password
    };

    users.push(newUser);

    localStorage.setItem(
      "ams_users",
      JSON.stringify(users)
    );

    return newUser;
  },

  // LOGIN
  login(email, password) {
    const users = JSON.parse(localStorage.getItem("ams_users") || "[]");

    const cleanEmail = email.trim().toLowerCase();

    const user = users.find(
      u =>
        u.email.toLowerCase() === cleanEmail &&
        u.password === password
    );

    if (!user) return null;

    const sessionUser = {
      name: user.name,
      email: user.email
    };

    localStorage.setItem(
      "ams_user",
      JSON.stringify(sessionUser)
    );

    return sessionUser;
  },

  logout() {
    localStorage.removeItem("ams_user");
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("ams_user"));
    } catch {
      return null;
    }
  },

  isLoggedIn() {
    return !!localStorage.getItem("ams_user");
  }
};

