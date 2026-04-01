namespace UiTime.Api.Core.Entities;

public class User
{
    public Guid Id { get; set; }
    public required long TelegramId { get; set; } 
    public string? Username { get; set; }
    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public ICollection<Lesson> Lessons { get; set; } = new List<Lesson>();
}