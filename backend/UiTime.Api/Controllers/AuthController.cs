using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using UiTime.Api.Core.DTOs;
using UiTime.Api.Core.Entities;
using UiTime.Api.Infrastructure.Data;

namespace UiTime.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly AppDbContext _context;
    private readonly IConfiguration _configuration;

    public AuthController(AppDbContext context, IConfiguration configuration)
    {
        _context = context;
        _configuration = configuration;
    }

    [HttpPost("login")]
    public async Task<ActionResult<AuthResponseDto>> Login([FromBody] LoginRequestDto request)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.TelegramId == request.TelegramId);
        
        if (user == null)
        {
            var invite = await _context.InviteCodes
                .FirstOrDefaultAsync(i => i.Code == request.InviteCode);

            if (invite == null || invite.IsUsed)
            {
                return Forbid("Invalid or already used invite code.");
            }
            
            user = new User
            {
                TelegramId = request.TelegramId,
                Username = request.Username
            };
            _context.Users.Add(user);
            
            if (invite.Code != "DEV_DEBUG_2026") 
            {
                invite.IsUsed = true;
            }
            
            invite.IsUsed = true;
            invite.UsedByTelegramId = request.TelegramId;

            await _context.SaveChangesAsync();
        }
        
        var token = GenerateJwtToken(user);

        return Ok(new AuthResponseDto(token, "Welcome to UiTime!"));
    }
    
    [HttpPost("generate-invite")]
    [AllowAnonymous]
    public async Task<IActionResult> GenerateInviteCode()
    {
        string newCodeValue;
        bool isUnique = false;

        do
        {
            newCodeValue = $"UI-{GenerateRandomString(6)}";
            isUnique = !await _context.InviteCodes.AnyAsync(c => c.Code == newCodeValue);
        } 
        while (!isUnique);
        
        var inviteCode = new InviteCode
        {
            Id = Guid.NewGuid(),
            Code = newCodeValue,
            IsUsed = false
        };
        
        _context.InviteCodes.Add(inviteCode);
        await _context.SaveChangesAsync();
        
        return Ok(new 
        { 
            Message = "Invite code generated successfully",
            InviteCode = inviteCode.Code 
        });
    }
    
    private string GenerateRandomString(int length)
    {
        const string chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        var random = new Random();
        return new string(Enumerable.Repeat(chars, length)
            .Select(s => s[random.Next(s.Length)]).ToArray());
    }
    
    private string GenerateJwtToken(User user)
    {
        var jwtSettings = _configuration.GetSection("JwtSettings");
        var secretKey = jwtSettings["SecretKey"]!;
        
        var securityKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secretKey));
        var credentials = new SigningCredentials(securityKey, SecurityAlgorithms.HmacSha256);
        
        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub, user.TelegramId.ToString()),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString())
        };

        var token = new JwtSecurityToken(
            issuer: jwtSettings["Issuer"],
            audience: jwtSettings["Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddDays(int.Parse(jwtSettings["ExpirationDays"]!)),
            signingCredentials: credentials);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}