from __future__ import annotations
from dataclasses import dataclass
import discord
import discord.abc
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.bot import Bot


@dataclass
class EventDispatcher:
    """
    Events dispatcher module. Please see https://discordpy.readthedocs.io/en/stable/api.html#event-reference

    To add new events:
    1. Create a new function (according to the discord.py's Event Reference) in this module
    2. Add the function to link_events
    3. Add the same function to src/basemodule.py BaseModule class
    4. Make sure this module's function calls both the bot.py's function AND each module's function in bot.modules

    Attributes:
        bot (Bot): the main bot object

    Examples:
        events = EventDispatcher(self)
        events.link_events()
    """

    bot: Bot

    def link_events(self):
        """Remember to have the same events in EventHandler as in EventDispatcher.

        See Also:
            https://discordpy.readthedocs.io/en/stable/api.html#event-reference
        """

        # following events are non discord events, and thus don't need to be registered to the discord client
        non_discord_events: list[str] = [
            'on_new_day'
        ]

        for attribute in dir(self):
            if not attribute.startswith('on_') or attribute in non_discord_events:
                continue
            if attribute not in dir(EventHandler):
                print(f"Warning! {attribute} is not found in src.events.EventHandler! Might cause an error runtime.")
            self.bot.client.event(getattr(self, attribute))

    async def handle_event(self, event_name: str, *args):
        await getattr(self.bot, event_name)(*args)
        for module in self.bot.modules:
            try:
                await getattr(module, event_name)(*args)
            except Exception as e:
                print(f"Module {module.__class__.__module__} failed {event_name}: {e}")

    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        await self.handle_event('on_audit_log_entry_create', entry)

    async def on_automod_action(self, execution: discord.AutoModAction):
        await self.handle_event('on_automod_action', execution)

    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        await self.handle_event('on_automod_rule_create', rule)

    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        await self.handle_event('on_automod_rule_delete', rule)

    async def on_automod_rule_update(self, rule: discord.AutoModRule):
        await self.handle_event('on_automod_rule_update', rule)

    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        await self.handle_event('on_bulk_message_delete', messages)

    async def on_connect(self):
        await self.handle_event('on_connect')

    async def on_disconnect(self):
        await self.handle_event('on_disconnect')

    async def on_error(self, event: str, *args, **kwargs):
        await self.handle_event('on_error', event, *args)

    async def on_guild_available(self, guild: discord.Guild):
        await self.handle_event('on_guild_available', guild)

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.handle_event('on_guild_channel_create', channel)

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.handle_event('on_guild_channel_delete', channel)

    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: datetime.datetime):
        await self.handle_event('on_guild_channel_pins_update', channel, last_pin)

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        await self.handle_event('on_guild_channel_update', before, after)

    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji],
                                     after: list[discord.Emoji]):
        await self.handle_event('on_guild_emojis_update', guild, before, after)

    async def on_guild_integrations_update(self, guild: discord.Guild):
        await self.handle_event('on_guild_integrations_update', guild)

    async def on_guild_join(self, guild: discord.Guild):
        await self.handle_event('on_guild_join', guild)

    async def on_guild_remove(self, guild: discord.Guild):
        await self.handle_event('on_guild_remove', guild)

    async def on_guild_role_create(self, role: discord.Role):
        await self.handle_event('on_guild_role_create', role)

    async def on_guild_role_delete(self, role: discord.Role):
        await self.handle_event('on_guild_role_delete', role)

    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        await self.handle_event('on_guild_role_update', before, after)

    async def on_guild_stickers_update(self, guild: discord.Guild, before: list[discord.GuildSticker],
                                       after: list[discord.GuildSticker]):
        await self.handle_event('on_guild_stickers_update', guild, before, after)

    async def on_guild_unavailable(self, guild: discord.Guild):
        await self.handle_event('on_guild_unavailable', guild)

    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        await self.handle_event('on_guild_update', before, after)

    async def on_integration_create(self, integration: discord.Integration):
        await self.handle_event('on_integration_create', integration)

    async def on_interaction(self, integration: discord.Integration):
        await self.handle_event('on_interaction', integration)

    async def on_integration_update(self, integration: discord.Integration):
        await self.handle_event('on_integration_update', integration)

    async def on_invite_create(self, invite: discord.Invite):
        await self.handle_event('on_invite_create', invite)

    async def on_invite_delete(self, invite: discord.Invite):
        await self.handle_event('on_invite_delete', invite)

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self.handle_event('on_member_ban', guild, user)

    async def on_member_join(self, member: discord.Member):
        await self.handle_event('on_member_join', member)

    async def on_member_remove(self, member: discord.Member):
        await self.handle_event('on_member_remove', member)

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.handle_event('on_member_unban', guild, user)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        await self.handle_event('on_member_update', before, after)

    async def on_message(self, message: discord.Message):
        await self.handle_event('on_message', message)

    async def on_message_delete(self, message: discord.Message):
        await self.handle_event('on_message_delete', message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.handle_event('on_message_edit', before, after)

    async def on_new_day(self, date_now: datetime):
        await self.handle_event('on_new_day', date_now)

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        await self.handle_event('on_presence_update', before, after)

    async def on_private_channel_create(self, channel: discord.abc.PrivateChannel):
        await self.handle_event('on_private_channel_create', channel)

    async def on_private_channel_delete(self, channel: discord.abc.PrivateChannel):
        await self.handle_event('on_private_channel_delete', channel)

    async def on_private_channel_pins_update(self, channel: discord.abc.PrivateChannel, last_pin: datetime.datetime):
        await self.handle_event('on_private_channel_pins_update', channel, last_pin)

    async def on_private_channel_update(self, before: discord.abc.PrivateChannel, after: discord.abc.PrivateChannel):
        await self.handle_event('on_private_channel_update', before, after)

    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        await self.handle_event('on_raw_bulk_message_delete', payload)

    async def on_raw_integration_delete(self, payload: discord.RawIntegrationDeleteEvent):
        await self.handle_event('on_raw_integration_delete', payload)

    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        await self.handle_event('on_raw_member_remove', payload)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        await self.handle_event('on_raw_message_delete', payload)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        await self.handle_event('on_raw_message_edit', payload)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.handle_event('on_raw_reaction_add', payload)

    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        await self.handle_event('on_raw_reaction_clear', payload)

    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        await self.handle_event('on_raw_reaction_clear_emoji', payload)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.handle_event('on_raw_reaction_remove', payload)

    async def on_raw_thread_update(self, payload: discord.RawThreadUpdateEvent):
        await self.handle_event('on_raw_thread_update', payload)

    async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent):
        await self.handle_event('on_raw_thread_delete', payload)

    async def on_raw_thread_member_remove(self, payload: discord.RawThreadMembersUpdate):
        await self.handle_event('on_raw_thread_member_remove', payload)

    async def on_raw_typing(self, payload: discord.RawTypingEvent):
        await self.handle_event('on_raw_typing', payload)

    async def on_ready(self):
        await self.handle_event('on_ready')

        self.bot.database.save_database()

        @self.bot.commands.register(command_name='reload_module', function=self.bot.reload_module,
                                    description='Reload module', commands_per_day=200, timeout=5)
        async def reload_module(interaction: discord.Interaction, module_name: str = ""):
            await self.bot.commands.commands['reload_module'].execute(
                user=self.bot.get_user_by_id(interaction.user.id),
                interaction=interaction,
                module_name=module_name
            )

        self.bot.client_tree.copy_global_to(guild=self.bot.server)
        await self.bot.client_tree.sync(guild=self.bot.server)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        await self.handle_event('on_reaction_add', reaction, user)

    async def on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        await self.handle_event('on_reaction_clear', message, reactions)

    async def on_reaction_clear_emoji(self, reaction: discord.Reaction):
        await self.handle_event('on_reaction_clear_emoji', reaction)

    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        await self.handle_event('on_reaction_remove', reaction, user)

    async def on_resumed(self):
        await self.handle_event('on_resumed')

    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        await self.handle_event('on_scheduled_event_create', event)

    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        await self.handle_event('on_scheduled_event_delete', event)

    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        await self.handle_event('on_scheduled_event_update', before, after)

    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        await self.handle_event('on_scheduled_event_user_add', event, user)

    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        await self.handle_event('on_scheduled_event_user_remove', event, user)

    async def on_shard_connect(self, shard_id: int):
        await self.handle_event('on_shard_connect', shard_id)

    async def on_shard_disconnect(self, shard_id: int):
        await self.handle_event('on_shard_disconnect', shard_id)

    async def on_shard_ready(self, shard_id: int):
        await self.handle_event('on_shard_ready', shard_id)

    async def on_shard_resumed(self, shard_id: int):
        await self.handle_event('on_shard_resumed', shard_id)

    async def on_socket_event_type(self, event_type: str):
        await self.handle_event('on_socket_event_type', event_type)

    async def on_socket_raw_receive(self, msg: bytes):
        await self.handle_event('on_socket_raw_receive', msg)

    async def on_socket_raw_send(self, payload: dict):
        await self.handle_event('on_socket_raw_send', payload)

    async def on_stage_instance_create(self, stage_instance: discord.StageInstance):
        await self.handle_event('on_stage_instance_create', stage_instance)

    async def on_stage_instance_delete(self, stage_instance: discord.StageInstance):
        await self.handle_event('on_stage_instance_delete', stage_instance)

    async def on_stage_instance_update(self, before: discord.StageInstance, after: discord.StageInstance):
        await self.handle_event('on_stage_instance_update', before, after)

    async def on_thread_create(self, thread: discord.Thread):
        await self.handle_event('on_thread_create', thread)

    async def on_thread_delete(self, thread: discord.Thread):
        await self.handle_event('on_thread_delete', thread)

    async def on_thread_join(self, thread: discord.Thread):
        await self.handle_event('on_thread_join', thread)

    async def on_thread_member_join(self, member: discord.ThreadMember):
        await self.handle_event('on_thread_member_join', member)

    async def on_thread_member_remove(self, member: discord.ThreadMember):
        await self.handle_event('on_thread_member_remove', member)

    async def on_thread_remove(self, thread: discord.Thread):
        await self.handle_event('on_thread_remove', thread)

    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        await self.handle_event('on_thread_update', before, after)

    async def on_typing(self, channel: discord.abc.Messageable, user: discord.User, when: datetime.datetime):
        await self.handle_event('on_typing', channel, user, when)

    async def on_user_update(self, before: discord.User, after: discord.User):
        await self.handle_event('on_user_update', before, after)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self.handle_event('on_voice_state_update', member, before, after)

    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        await self.handle_event('on_webhooks_update', channel)


@dataclass
class EventHandler:
    """Event Dispatcher Class.

    bot.Bot and the BaseModule in modules.module use this as their base class.

    See Also:
        https://discordpy.readthedocs.io/en/stable/api.html
    """

    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        pass

    async def on_automod_action(self, execution: discord.AutoModAction):
        pass

    async def on_automod_rule_create(self, rule: discord.AutoModRule):
        pass

    async def on_automod_rule_delete(self, rule: discord.AutoModRule):
        pass

    async def on_automod_rule_update(self, rule: discord.AutoModRule):
        pass

    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        pass

    async def on_connect(self):
        pass

    async def on_disconnect(self):
        pass

    async def on_error(self, event: str, *args, **kwargs):
        pass

    async def on_guild_available(self, guild: discord.Guild):
        pass

    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        pass

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        pass

    async def on_guild_channel_pins_update(self, channel: discord.abc.GuildChannel, last_pin: datetime.datetime):
        pass

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        pass

    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji],
                                     after: list[discord.Emoji]):
        pass

    async def on_guild_integrations_update(self, guild: discord.Guild):
        pass

    async def on_guild_join(self, guild: discord.Guild):
        pass

    async def on_guild_remove(self, guild: discord.Guild):
        pass

    async def on_guild_role_create(self, role: discord.Role):
        pass

    async def on_guild_role_delete(self, role: discord.Role):
        pass

    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        pass

    async def on_guild_stickers_update(self, guild: discord.Guild, before: list[discord.GuildSticker],
                                       after: list[discord.GuildSticker]):
        pass

    async def on_guild_unavailable(self, guild: discord.Guild):
        pass

    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        pass

    async def on_integration_create(self, integration: discord.Integration):
        pass

    async def on_interaction(self, integration: discord.Integration):
        pass

    async def on_integration_update(self, integration: discord.Integration):
        pass

    async def on_invite_create(self, invite: discord.Invite):
        pass

    async def on_invite_delete(self, invite: discord.Invite):
        pass

    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        pass

    async def on_member_join(self, member: discord.Member):
        pass

    async def on_member_remove(self, member: discord.Member):
        pass

    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        pass

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        pass

    async def on_message(self, message: discord.Message):
        pass

    async def on_message_delete(self, message: discord.Message):
        pass

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        pass

    async def on_new_day(self, date_now: datetime):
        pass

    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        pass

    async def on_private_channel_create(self, channel: discord.abc.PrivateChannel):
        pass

    async def on_private_channel_delete(self, channel: discord.abc.PrivateChannel):
        pass

    async def on_private_channel_pins_update(self, channel: discord.abc.PrivateChannel, last_pin: datetime.datetime):
        pass

    async def on_private_channel_update(self, before: discord.abc.PrivateChannel, after: discord.abc.PrivateChannel):
        pass

    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        pass

    async def on_raw_integration_delete(self, payload: discord.RawIntegrationDeleteEvent):
        pass

    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        pass

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        pass

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        pass

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        pass

    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        pass

    async def on_raw_reaction_clear_emoji(self, payload: discord.RawReactionClearEmojiEvent):
        pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        pass

    async def on_raw_thread_update(self, payload: discord.RawThreadUpdateEvent):
        pass

    async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent):
        pass

    async def on_raw_thread_member_remove(self, payload: discord.RawThreadMembersUpdate):
        pass

    async def on_raw_typing(self, payload: discord.RawTypingEvent):
        pass

    async def on_ready(self):
        pass

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        pass

    async def on_reaction_clear(self, message: discord.Message, reactions: list[discord.Reaction]):
        pass

    async def on_reaction_clear_emoji(self, reaction: discord.Reaction):
        pass

    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        pass

    async def on_resumed(self):
        pass

    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        pass

    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        pass

    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        pass

    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        pass

    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        pass

    async def on_shard_connect(self, shard_id: int):
        pass

    async def on_shard_disconnect(self, shard_id: int):
        pass

    async def on_shard_ready(self, shard_id: int):
        pass

    async def on_shard_resumed(self, shard_id: int):
        pass

    async def on_socket_event_type(self, event_type: str):
        pass

    async def on_socket_raw_receive(self, msg: bytes):
        pass

    async def on_socket_raw_send(self, payload: dict):
        pass

    async def on_stage_instance_create(self, stage_instance: discord.StageInstance):
        pass

    async def on_stage_instance_delete(self, stage_instance: discord.StageInstance):
        pass

    async def on_stage_instance_update(self, before: discord.StageInstance, after: discord.StageInstance):
        pass

    async def on_thread_create(self, thread: discord.Thread):
        pass

    async def on_thread_delete(self, thread: discord.Thread):
        pass

    async def on_thread_join(self, thread: discord.Thread):
        pass

    async def on_thread_member_join(self, member: discord.ThreadMember):
        pass

    async def on_thread_member_remove(self, member: discord.ThreadMember):
        pass

    async def on_thread_remove(self, thread: discord.Thread):
        pass

    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        pass

    async def on_typing(self, channel: discord.abc.Messageable, user: discord.User, when: datetime.datetime):
        pass

    async def on_user_update(self, before: discord.User, after: discord.User):
        pass

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        pass

    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        pass
