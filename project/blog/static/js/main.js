const taskInput = document.getElementById("task");
const addBtn = document.getElementById("add");
const taskList = document.getElementById("taskList");
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

addBtn.addEventListener("click", () => {
    const taskText = taskInput.value.trim();
    if (taskText !== "") {
        fetch("http://127.0.0.1:8000/api/tasks/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ title: taskText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                createTask(data.title, data.id,data.completed); // use task id from backend
                taskInput.value = "";
            } else {
                alert("Failed to add task: " + (data.error || ""));
            }
        })
        .catch(error => console.error("Error adding task:", error));
    }
});

fetch('http://127.0.0.1:8000/api/tasks/')
  .then(response => response.json())
  .then(data => {
    console.log(data.tasks);
    data.tasks.forEach(task => {
      createTask(task.title, task.id , task.completed );
    });
  })
  .catch(error => console.error('Error fetching tasks:', error));
function createTask(text, id ,completed) {
    const taskItem = document.createElement("li");
    
   taskItem.innerHTML = completed 
  ? `<span class="completed">${text}</span><button class="delete">Delete</button>`
  : `<span>${text}</span><button class="delete">Delete</button>`;

    taskList.appendChild(taskItem);
    const deleteBtn = taskItem.querySelector(".delete");
    deleteBtn.addEventListener("click", () => {
        fetch(`http://127.0.0.1:8000/api/tasks/${id}/`, { 
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => {
            if (response.ok) {
                taskItem.remove();
            } else {
                alert("Failed to delete task");
            }
        });
    });

    taskItem.addEventListener("click", () => {
        fetch(`http://127.0.0.1:8000/api/tasks/${id}/complete/`, { method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(res => res.json())
        .then(data => console.log(data));
        taskItem.classList.toggle("completed");
    });
}
