using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.AspNetCore.Http;


var builder = WebApplication.CreateSlimBuilder(new WebApplicationOptions {
    Args = args,
    ContentRootPath = AppContext.BaseDirectory
});


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

// Disable all logging for a fair benchmark (writing to console kills RPS)
builder.Logging.ClearProviders();


var app = builder.Build();

if (mode == "api") {
    app.MapGet("/", () => Results.Ok("Hello world!"));
} else if (mode == "yarp") {
    app.MapReverseProxy();
}

app.Run();
