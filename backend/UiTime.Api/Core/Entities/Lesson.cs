namespace UiTime.Api.Core.Entities;

public class Lesson
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public Guid SubjectId { get; set; }

    public DateTimeOffset StartTime { get; set; }
    public DateTimeOffset EndTime { get; set; }

    public string? Location { get; set; } 
    public string? OnlineLink { get; set; } 
    
    public User User { get; set; } = null!;
    public Subject Subject { get; set; } = null!;
}