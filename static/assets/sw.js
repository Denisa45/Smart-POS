self.addEventListener("push", function(event) {
    const data = event.data ? event.data.json() : {};
    self.registration.showNotification(data.title || "Smart POS", {
        body: data.body || "Your order is ready!",
        icon: "/static/assets/icon.png"
    });
});
