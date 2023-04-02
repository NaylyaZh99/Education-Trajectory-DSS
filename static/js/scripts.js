console.log("JavaScript code running");

var coll = document.getElementsByClassName("collapsible");
var i;

console.log("Found", coll.length, "collapsible elements");

for (i = 0; i < coll.length; i++) {
    console.log("Attaching click listener to element", coll[i]);
    coll[i].addEventListener("click", function() {
        console.log("Button clicked!");
        this.classList.toggle("active");
        var table = document.getElementById("table_" + this.id.split("_")[1]);
        if (table.style.display === "block") {
            table.style.display = "none";
        } else {
            table.style.display = "block";
        }
    });
}