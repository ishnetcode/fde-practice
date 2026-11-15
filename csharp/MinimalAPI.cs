var app = WebApplication.Create();
app.MapGet("/quotes/{id}", (int id) => new { Id = id, Status = "found" });
app.Run();