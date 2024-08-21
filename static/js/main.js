
let progresso = 0;

const progresso_bar = document.getElementById('#progresso');

function incrementarProgresso(){
    if(progresso < 100){
        progresso += 10;
        progresso_bar.style.width = progresso + '%';
        progresso_bar.textContent = progresso + '%';
    }
}
