
async function verificarLogin() {
    const cookie = localStorage.getItem("cookie");

    if (!cookie) {
        alert("No estás logueado. Redirigiendo al login...");
        window.location.href = "login.html";
        return;
    }

    try {
        // Verificamos la cookie con el servidor
        const respuesta = await fetch("http://127.0.0.1:5000/verificar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ cookie }),
        });

        if (!respuesta.ok) {
            alert("Tu sesión ha expirado. Redirigiendo al login...");
            localStorage.removeItem("cookie");
            localStorage.removeItem("usuario");
            window.location.href = "login.html";
        } else { // ta loged

        }
    } catch (error) {
        console.error("Error al verificar la sesión:", error);
        alert("Hubo un problema al verificar tu sesión");
    }
}

async function logout() {
    const cookie = localStorage.getItem("cookie");

    if (!cookie) {
        alert("No estás logueado.");
        return;
    }

    try {
        // Enviamos la cookie al servidor para eliminarla
        const respuesta = await fetch("http://127.0.0.1:5000/logout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ cookie }),
        });

        if (respuesta.ok) {
            // Eliminamos la cookie del localStorage
            localStorage.removeItem("cookie");
            localStorage.removeItem("usuario");

            alert("Has cerrado sesión correctamente.");
            window.location.href = "login.html";
        } else {
            alert("Hubo un problema al cerrar la sesión.");
        }
    } catch (error) {
        console.error("Error al cerrar sesión:", error);
        alert("Error al conectar con el servidor.");
    }
}

// Ejecutamos la verificación al cargar la página
window.onload = verificarLogin;

async function loadFeed() {
    const username = localStorage.getItem("usuario");

    try {
        const response = await fetch(`http://127.0.0.1:5000/feed?user=${username}`);
        if (!response.ok) throw new Error("Error al cargar el feed");

        const data = await response.json();

        // Mostrar usuario principal
        const userDiv = document.getElementById("current-user");
        userDiv.innerHTML = `
                <div class="user-card" onclick="goToProfile('${data.currentUser.username}')">
                <div class="circle"></div>
                <span>${data.currentUser.name} ${data.currentUser.surname} (@${data.currentUser.username})</span>
                </div>
                `;

        // Mostrar recomendaciones con botón dinámico
        const recommendationsDiv = document.getElementById("recommendations");
        recommendationsDiv.innerHTML = "";

        data.recommendations.forEach(user => {
            recommendationsDiv.innerHTML += `
                <div class="user-card">
                <div class="circle"></div>
                <span onclick="goToProfile('${user.username}')">${user.name} ${user.surname}</span>
                <button id="follow-btn-${user.username}" onclick="toggleFollow('${user.username}', this)">Seguir</button>
                </div>
                `;
        });



    } catch (error) {
        console.error("Error al cargar el feed:", error);
        alert("Hubo un problema al cargar el feed.");
    }
}


// Redirigir al perfil del usuario
function goToProfile(username) {
    window.location.href = `profile.html?user=${username}`;
}

// Publicar contenido
async function postContent(event) {
    event.preventDefault();

    const username = localStorage.getItem("usuario");
    const content = document.getElementById("post-content").value;

    const response = await fetch("http://127.0.0.1:5000/post", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ user: username, content }),
    });

    if (response.ok) {
        alert("¡Publicación creada con éxito!");
        document.getElementById("post-content").value = ""; // Limpiar el área de texto
        location.reload();

    } else {
        alert("Hubo un problema al publicar.");
    }
}


async function loadPosts() {
    const username = localStorage.getItem("usuario");

    try {
        const response = await fetch(`http://127.0.0.1:5000/posts?user=${username}`);
        if (!response.ok) throw new Error("Error al cargar los posts");

        const posts = await response.json();

        const postsDiv = document.getElementById("posts");
        postsDiv.innerHTML = ""; // Limpiar el contenido previo

        posts.forEach(post => {
            postsDiv.innerHTML += `
                <div class="post-card">
                    <strong>${post.author_name} ${post.author_surname} (@${post.author_username}):</strong>
                    <p>${post.content}</p>
                    <small>${post.date}</small>
                    <div class="like-container">
                        <button id="like-btn-${post.id}" class="like-btn" onclick="toggleLike('${post.id}')">
                            ${post.liked ? "Dislike" : "Like"}
                        </button>
                        <span id="likes-count-${post.id}" class="likes-count">${post.likes} likes</span>
                    </div>
                    ${post.author_username === username
                    ? `<button class="delete-btn" onclick="deletePost('${post.id}')">✖</button>`
                    : ""}
                    <div class="comments-section">
                        <div id="comments-${post.id}"></div>
                        <textarea id="comment-input-${post.id}" placeholder="Escribe un comentario..."></textarea>
                        <button onclick="addComment('${post.id}')">Comentar</button>
                    </div>
                </div>
            `;
            loadComments(post.id); // Cargar comentarios de cada post
        });

    } catch (error) {
        console.error("Error al cargar los posts:", error);
        alert("Hubo un problema al cargar los posts.");
    }
}





window.onload = async function () {
    await verificarLogin();  // Verificar la sesión
    await loadFeed();        // Cargar usuario y recomendaciones
    await loadPosts();       // Cargar posts
};


async function toggleFollow(username, button) {
    const current_user = localStorage.getItem("usuario");

    if (button.innerText === "Seguir") {
        // Seguir al usuario
        try {
            const response = await fetch("http://127.0.0.1:5000/follow", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_user, user_to_follow: username })
            });

            if (response.ok) {
                alert("¡Usuario seguido exitosamente!");
                button.innerText = "Unfollow";
            } else {
                alert("Hubo un problema al seguir al usuario.");
            }
        } catch (error) {
            console.error("Error al seguir al usuario:", error);
        }
    } else {
        // Dejar de seguir al usuario
        try {
            const response = await fetch("http://127.0.0.1:5000/unfollow", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_user, user_to_unfollow: username })
            });

            if (response.ok) {
                alert("¡Usuario dejado de seguir exitosamente!");
                button.innerText = "Seguir";
            } else {
                alert("Hubo un problema al dejar de seguir al usuario.");
            }
        } catch (error) {
            console.error("Error al dejar de seguir al usuario:", error);
        }
    }
}

async function deletePost(post_id) {
    if (!confirm("¿Estás seguro de que deseas eliminar esta publicación?")) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/delete_post", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ post_id }),
        });

        if (response.ok) {
            alert("Publicación eliminada correctamente.");
            // Recargar los posts después de eliminar
            await loadPosts();
        } else {
            alert("Hubo un problema al eliminar la publicación.");
        }
    } catch (error) {
        console.error("Error al eliminar la publicación:", error);
    }
}

async function toggleLike(post_id) {
    const current_user = localStorage.getItem("usuario");

    try {
        const response = await fetch("http://127.0.0.1:5000/toggle-like", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: current_user, post_id: post_id }),
        });

        if (response.ok) {
            const result = await response.json();
            const likeBtn = document.getElementById(`like-btn-${post_id}`);
            const likesCount = document.getElementById(`likes-count-${post_id}`);
            if (result.message === "Post liked") {
                likeBtn.innerText = "Dislike";
                likesCount.innerText = parseInt(likesCount.innerText) + 1;
            } else if (result.message === "Post unliked") {
                likeBtn.innerText = "Like";
                likesCount.innerText = parseInt(likesCount.innerText) - 1;
            } else {
                alert("Hubo un problema al cambiar el estado del like.");
            }
        } else {
            alert("Hubo un problema al cambiar el estado del like.");
        }
    } catch (error) {
        console.error("Error al cambiar el estado del like:", error);
        alert("Error al conectar con el servidor.");
    }
}


async function addComment(post_id) {
    const commentInput = document.getElementById(`comment-input-${post_id}`);
    const commentText = commentInput.value;
    const username = localStorage.getItem("usuario");

    if (!commentText) {
        alert("El comentario no puede estar vacío.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/comment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: username, post_id: post_id, comment: commentText }),
        });

        if (response.ok) {
            commentInput.value = ""; // Limpiar el campo de texto
            loadComments(post_id); // Recargar comentarios
        } else {
            alert("Hubo un problema al agregar el comentario.");
        }
    } catch (error) {
        console.error("Error al agregar el comentario:", error);
    }
}

async function loadComments(post_id) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/comments?post_id=${post_id}`);
        if (!response.ok) throw new Error("Error al cargar los comentarios");

        const comments = await response.json();
        const commentsDiv = document.getElementById(`comments-${post_id}`);
        commentsDiv.innerHTML = ""; // Limpiar los comentarios previos

        comments.forEach(comment => {
            commentsDiv.innerHTML += `
        <div class="comment">
            <div>
                <strong>${comment.author_name} ${comment.author_surname} (@${comment.author_username}):</strong>
                <p>${comment.text}</p>
                <small>${comment.date}</small>
            </div>
            ${comment.author_username === localStorage.getItem("usuario")
                    ? `<button class="delete-btn" onclick="deleteComment('${post_id}', '${comment.text}')">✖</button>`
                    : ""
                }
        </div>
    `;
        });

    } catch (error) {
        console.error("Error al cargar los comentarios:", error);
    }
}

async function deleteComment(post_id, comment_text) {
    const username = localStorage.getItem("usuario");

    if (!confirm("¿Estás seguro de que deseas eliminar este comentario?")) return;

    try {
        const response = await fetch("http://127.0.0.1:5000/delete_comment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: username, post_id: post_id, comment_text: comment_text }),
        });

        if (response.ok) {
            alert("Comentario eliminado correctamente.");
            loadComments(post_id); // Recargar los comentarios del post
        } else {
            alert("Hubo un problema al eliminar el comentario.");
        }
    } catch (error) {
        console.error("Error al eliminar el comentario:", error);
    }
}






function renderSearchResults(users) {
    const resultsDiv = document.getElementById("search-results");
    resultsDiv.innerHTML = ""; // Limpiar resultados previos

    if (users.length === 0) {
        resultsDiv.innerHTML = "<p>No se encontraron usuarios</p>";
        return;
    }

    users.forEach(user => {
        const buttonText = user.is_following ? "Unfollow" : "Seguir";
        const buttonClass = user.is_following ? "btn-unfollow" : "btn-follow";

        resultsDiv.innerHTML += `
            <div class="search-result">
                <span onclick="goToProfile('${user.username}')">${user.name} ${user.surname} (@${user.username})</span>
                <button id="follow-btn-${user.username}" class="${buttonClass}" onclick="toggleFollow('${user.username}', this)">
                    ${buttonText}
                </button>
            </div>
        `;
    });
}



document.getElementById("user-search-input").addEventListener("input", (event) => {
    const query = event.target.value.trim();
    const currentUser = localStorage.getItem("usuario");
    if (query.length > 0) {
        searchUsers(query, currentUser);
    } else {
        document.getElementById("search-results").innerHTML = ""; // Limpiar resultados si está vacío
    }
});

async function searchUsers(query, currentUser) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/search_users?query=${encodeURIComponent(query)}&current_user=${encodeURIComponent(currentUser)}`);
        if (!response.ok) throw new Error("Error al buscar usuarios");

        const users = await response.json();
        renderSearchResults(users);
    } catch (error) {
        console.error("Error al buscar usuarios:", error);
        alert("Hubo un problema al buscar usuarios.");
    }
}

