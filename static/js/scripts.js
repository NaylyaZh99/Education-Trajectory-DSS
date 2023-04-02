console.log("JavaScript code running");

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var table = document.getElementById("table_" + this.id.split("_")[1]);
        if (table.style.display === "block") {
            table.style.display = "none";
        } else {
            table.style.display = "block";
        }
    });
}