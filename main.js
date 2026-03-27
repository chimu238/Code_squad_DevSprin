document.addEventListener("DOMContentLoaded", function () {
  const tabs = document.querySelectorAll(".tab");
  const cards = document.querySelectorAll(".request-card");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const filter = tab.dataset.filter; 

      cards.forEach(card => {
        if (filter === "all") {
          card.style.display = "block";
        } else if (card.classList.contains(filter)) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
        
        window.location.href = "foldername/dashboard.html";
        async function accept(id) {
    await fetch("http://127.0.0.1:5000/accept", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({id})
    });
    loadRequests(); // refresh
}

async function deliver(id) {
    await fetch("http://127.0.0.1:5000/deliver", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({id})
    });
    loadRequests(); // refresh
}
        
      });
    });
  });
});
