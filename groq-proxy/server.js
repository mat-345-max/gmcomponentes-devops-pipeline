const app = require('./app');

const port = process.env.PORT || 8787;
app.listen(port, () => {
  console.log(`Groq proxy escuchando en http://localhost:${port}`);
});