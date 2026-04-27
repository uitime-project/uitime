# Build
FROM mcr.microsoft.com/dotnet/sdk:10:0 as AS build
WORKDIR /src

# Copy files and build
COPY . .
RUN dotnet restore "UiTime.Api.csproj"
RUN dotnet restore "UiTime.Api.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Run
FROM mcr.microsoft.com/dotnet/sdk:10:0 as AS final
WORKDIR /app
COPY --from=build /app/publish.

# Listen on potrt 8080 inside the container
ENV ASPNETCORE_HTTP_PORTS=8080

ENTRYPOINT["dotnet", "UiTime.Api.dll"]