document.addEventListener("DOMContentLoaded", async function () {

  const cards = document.querySelectorAll(".gd-match-card");

  for (const card of cards) {

    try {

      const data = JSON.parse(card.dataset.json);

      const responseA = await fetch(`/api/time-info?nome=${encodeURIComponent(data.time_a)}`);
      const timeA = await responseA.json();

      const responseB = await fetch(`/api/time-info?nome=${encodeURIComponent(data.time_b)}`);
      const timeB = await responseB.json();

      card.innerHTML = `
        <div class="gd-match-card-rendered">
          <div class="gd-match-team">
            <img src="${timeA.escudo_url}" loading="lazy">
            <span>${data.time_a}</span>
          </div>

          <div class="gd-match-center">
            <strong>${data.data} - ${data.horario}</strong>
            <span>${data.liga}</span>
          </div>

          <div class="gd-match-team">
            <img src="${timeB.escudo_url}" loading="lazy">
            <span>${data.time_b}</span>
          </div>
        </div>
      `;

    } catch (error) {
      console.error("Erro ao renderizar confronto:", error);
    }
  }

});
