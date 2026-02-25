<script>
document.addEventListener("DOMContentLoaded", async function() {

  const cards = document.querySelectorAll(".gd-match-card");

  for (const card of cards) {

    const data = JSON.parse(card.dataset.json);

    const responseA = await fetch(`/api/time-info?nome=${data.time_a}`);
    const timeA = await responseA.json();

    const responseB = await fetch(`/api/time-info?nome=${data.time_b}`);
    const timeB = await responseB.json();

    card.innerHTML = `
      <div class="gd-match-card-rendered">
        <div class="gd-match-team">
          <img src="${timeA.escudo_url}" loading="lazy">
          <span>${data.time_a}</span>
        </div>

        <div class="gd-match-center">
          <strong>${data.data}</strong>
          <span>${data.liga}</span>
          <span>${data.horario}</span>
        </div>

        <div class="gd-match-team">
          <img src="${timeB.escudo_url}" loading="lazy">
          <span>${data.time_b}</span>
        </div>
      </div>
    `;
  }

});
</script>
