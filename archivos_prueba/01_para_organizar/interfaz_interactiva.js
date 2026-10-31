document.addEventListener("DOMContentLoaded", () => {
  console.log("FilesPy UI cargada exitosamente");
  const btn = document.querySelector("#btn-accion");
  if (btn) btn.onclick = () => alert("Acción ejecutada");
});
