namespace UiTime.Api.Core.DTOs;

public record LoginRequestDto(
    long TelegramId, 
    string Username, 
    string InviteCode
);

public record AuthResponseDto(
    string Token, 
    string Message
);