namespace UiTime.Api.Core.Entities;

public class Subject
{
    public Guid Id { get; set; }
    public required string Name { get; set; } 
    public SubjectType Type { get; set; }
    public bool? HasExam { get; set; }
    public DateTimeOffset? ExamDate { get; set; } 
}