using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Http;

// Используем SlimBuilder, который выкидывает вообще весь лишний встроенный функционал ASP.NET
// (метрики, избыточный DI, дефолтные проверки), оставляя самый голый и быстрый пайплайн.
var builder = WebApplication.CreateSlimBuilder(args);

// Отключаем вообще всё логирование для честного бенчмарка (вывод в консоль убивает RPS)
builder.Logging.ClearProviders();

// Оптимизации Kestrel для максимальной пропускной способности
builder.WebHost.ConfigureKestrel(options => {
    options.AddServerHeader = false;
    options.AllowSynchronousIO = false;
});


var mode = builder.Configuration.GetValue<string>("mode")?.ToLowerInvariant() ?? "api";

if (mode == "yarp") {
    builder.Services
        .AddReverseProxy()
        .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));
}

var app = builder.Build();

if (mode == "api") {
    app.MapGet("/hello", () => Results.Ok("Hello world!"));
    app.MapGet("/", () => Results.Ok("Target API Server Running."));
} else if (mode == "yarp") {
    app.MapReverseProxy();
}

app.Run();
