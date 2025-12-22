```html
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body>
    <div class="card">
        <img src="i0.png">
    </div>
</body>

<style>
    @font-face {
        font-family: "Artifika";
        src: url("Artifika-Regular.ttf") format("truetype");
        font-display: swap;
    }

    * {
        box-sizing: border-box;
    }

    html {
        margin: 0;
        padding: 0;
        line-height: 1.75;
        font-size: 1.25em;
        font-family: "Artifika", system-ui, -apple-system, "Segoe UI", sans-serif;
        color: #1c1c1c;
        height: 100%;
    }


    body {
        background: rgb(184, 72, 27);
        background-image: radial-gradient(rgb(126, 48, 17) 5%, transparent 0);
        background-size: 35px 35px;
        height: 100%;
        width: 100%;
        margin: 0;
        padding: 5vh;
        overflow: hidden;
    }

    .card {
        display: flex;
        justify-content: center;
        align-items: center;
        background: white;
        border-radius: 5vh;
        padding: 5vh;
        height: 100%;
        width: 100%;
        margin: 0;
    }


    img {
        max-width: 100%;
        max-height: 100%;
    }

    @page {
        size: 1920px 1080px;
        margin: 0;
    }

    html,
    body {
        margin: 0;
        width: 1920px;
        height: 1080px;
    }
</style>

</html>
```