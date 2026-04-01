namespace UiTime.Api.Core.Entities;

public class InviteCode
{
    public Guid Id { get; set; }
    public required string Code { get; set; } 
    public bool IsUsed { get; set; }
    public long? UsedByTelegramId { get; set; }
}