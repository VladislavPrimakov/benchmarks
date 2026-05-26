using System;
using System.Threading;
using System.Threading.Tasks;
using zerg;
using zerg.Engine;
using zerg.Engine.Configs;
using zerg.core;

namespace ZergBenchmark
{
    class Program
    {
        private static readonly byte[] s_response =
            "HTTP/1.1 200 OK\r\nContent-Length: 12\r\nContent-Type: text/plain\r\n\r\nHello world!"u8.ToArray();

        static async Task Main(string[] args)
        {
            ushort port = 5005;
            if (args.Length > 0 && ushort.TryParse(args[0], out ushort parsedPort))
            {
                port = parsedPort;
            }

            int reactorCount = Environment.ProcessorCount;
            var engine = new Engine(new EngineOptions
            {
                Ip = "0.0.0.0",
                Port = port,
                ReactorCount = reactorCount,
                AcceptorConfig = new AcceptorConfig(IPVersion: IPVersion.IPv6DualStack)
            });

            engine.Listen();

            while (engine.ServerRunning)
            {
                var connection = await engine.AcceptAsync(CancellationToken.None);
                if (connection is null) continue;
                _ = HandleConnectionAsync(connection);
            }
        }

        static async Task HandleConnectionAsync(Connection connection)
        {
            try
            {
                while (true)
                {
                    var result = await connection.ReadAsync();
                    if (result.IsClosed) break;

                    var rings = connection.GetAllSnapshotRingsAsUnmanagedMemory(result);
                    var sequence = rings.ToReadOnlySequence();

                    int reqCount = 0;
                    var getBytes = "GET "u8;
                    foreach (var memory in sequence)
                    {
                        var span = memory.Span;
                        int index;
                        while ((index = span.IndexOf(getBytes)) >= 0)
                        {
                            reqCount++;
                            span = span.Slice(index + getBytes.Length);
                        }
                    }
                    if (reqCount == 0) reqCount = 1;

                    foreach (var ring in rings)
                    {
                        connection.ReturnRing(ring.BufferId);
                    }

                    for (int i = 0; i < reqCount; i++)
                    {
                        connection.Write(s_response);
                    }

                    await connection.FlushAsync();
                    connection.ResetRead();
                }
            }
            catch { }
            finally
            {
                connection.Dispose();
            }
        }
    }
}
