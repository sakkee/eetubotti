from PIL import Image, ImageDraw, ImageFont


class CardConstants:
    asset_directory: str = 'assets/stats/'
    card_bg_filename: str = asset_directory + 'card_base.png'
    card_front_filename: str = asset_directory + 'card_fullxp.png'
    NameFont: ImageFont.FreeTypeFont = ImageFont.truetype(asset_directory + 'comic.ttf', 40)
    NameColor: tuple[int, int, int] = (255, 255, 255)
    NamePosition: tuple[int, int] = (270, 125)
    ProfileSize: tuple[int, int] = (170, 170)
    ProfilePosition: tuple[int, int] = (37, 56)
    SmallFont: ImageFont.FreeTypeFont = ImageFont.truetype(asset_directory + 'comic.ttf', 25)
    IdentifierColor: tuple[int, int, int] = (130, 130, 130)
    IdentifierOffset: tuple[int, int] = (10, 0)
    RightOffset: int = 45
    XPOffsetWidth: int = 5
    LevelColor: tuple[int, int, int] = (100, 210, 245)
    LevelTopOffset: int = 95
    BigFont: ImageFont.FreeTypeFont = ImageFont.truetype(asset_directory + 'comic.ttf', 50)
    LeftX: int = 258
    RightX: int = 44


class Card:
    card_bg: Image.Image = Image.open(CardConstants.card_bg_filename)
    card_front: Image.Image = Image.open(CardConstants.card_front_filename)

    @classmethod
    def create_card(cls, xp: int, xp_to_next_level: int, rank: int, level: int, name: str, identifier: str,
                    profile_filepath: str) -> Image.Image:
        # initiate Images
        background = Image.new('RGBA', (cls.card_bg.width, cls.card_bg.height))
        card_bg = cls.card_bg.copy()
        card_front = cls.card_front.copy()
        profile_file = Image.open(profile_filepath).resize(CardConstants.ProfileSize)

        # create xp overlay
        proportion = xp / xp_to_next_level
        card_front = card_front.crop(
            (0,
             0,
             CardConstants.LeftX + int((card_front.width - CardConstants.LeftX - CardConstants.RightX) * proportion),
             card_front.height)
        )
        card_bg.paste(card_front)
        background.paste(profile_file, CardConstants.ProfilePosition)

        full_image = Image.alpha_composite(background, card_bg)
        full_imagedraw = ImageDraw.Draw(full_image)

        # draw name text
        if len(name) > 12:
            name = name[:12] + '...'
        full_imagedraw.text(CardConstants.NamePosition, name, fill=CardConstants.NameColor, font=CardConstants.NameFont)

        # draw identifier text
        name_w, name_h = full_imagedraw.textsize(name, font=CardConstants.NameFont)
        realname_w, realname_h = full_imagedraw.textsize('Salsi', font=CardConstants.NameFont)
        identifier_w, identifier_h = full_imagedraw.textsize('#' + str(identifier), font=CardConstants.SmallFont)
        if identifier and identifier != '0':
            full_imagedraw.text((CardConstants.NamePosition[0] + name_w + CardConstants.IdentifierOffset[0],
                                 CardConstants.NamePosition[1] + (realname_h - identifier_h)),
                                '#' + str(identifier), font=CardConstants.SmallFont, fill=CardConstants.IdentifierColor)

        # draw xp later text
        xp_later = '/{:0.2f}k XP'.format(xp_to_next_level / 1000.0)
        xp_later_w, xp_later_h = full_imagedraw.textsize(xp_later, font=CardConstants.SmallFont)
        full_imagedraw.text(
            (background.width - CardConstants.RightOffset - xp_later_w,
             CardConstants.NamePosition[1] + realname_h - identifier_h),
            xp_later, font=CardConstants.SmallFont, fill=CardConstants.IdentifierColor)

        # draw xp now text
        xp_now = '{:0.2f}k'.format(xp / 1000.0)
        xp_now_w, xp_now_h = full_imagedraw.textsize(xp_now, font=CardConstants.SmallFont)
        full_imagedraw.text(
            (background.width - CardConstants.RightOffset - xp_later_w - CardConstants.XPOffsetWidth - xp_now_w,
             CardConstants.NamePosition[1] + realname_h - identifier_h),
            xp_now, font=CardConstants.SmallFont, fill=CardConstants.NameColor)

        # level texts
        lvl_text1 = str(level)
        lvl_text1_w, lvl_text1_h = full_imagedraw.textsize(lvl_text1, font=CardConstants.BigFont)
        full_imagedraw.text(
            (background.width - CardConstants.RightOffset - lvl_text1_w, CardConstants.LevelTopOffset - lvl_text1_h),
            lvl_text1, font=CardConstants.BigFont, fill=CardConstants.LevelColor)

        lvl_text2 = 'LEVEL'
        lvl_text2_w, lvl_text2_h = full_imagedraw.textsize(lvl_text2, font=CardConstants.SmallFont)
        full_imagedraw.text(
            (background.width - CardConstants.RightOffset - lvl_text1_w - lvl_text2_w - CardConstants.XPOffsetWidth,
             CardConstants.LevelTopOffset - lvl_text2_h),
            lvl_text2, font=CardConstants.SmallFont, fill=CardConstants.LevelColor)

        lvl_text3 = '#' + str(rank)
        lvl_text3_w, lvl_text3_h = full_imagedraw.textsize(lvl_text3, font=CardConstants.BigFont)
        full_imagedraw.text((
            background.width - CardConstants.XPOffsetWidth * 3 - lvl_text1_w - lvl_text2_w - lvl_text3_w -
            CardConstants.RightOffset,
            CardConstants.LevelTopOffset - lvl_text3_h),
            lvl_text3, font=CardConstants.BigFont, fill=CardConstants.NameColor)

        lvl_text4 = 'RANK'
        lvl_text4_w, lvl_text4_h = full_imagedraw.textsize(lvl_text4, font=CardConstants.SmallFont)
        full_imagedraw.text((
            background.width - CardConstants.XPOffsetWidth * 4 - lvl_text1_w - lvl_text2_w - lvl_text3_w -
            CardConstants.RightOffset - lvl_text4_w,
            CardConstants.LevelTopOffset - lvl_text4_h),
            lvl_text4, font=CardConstants.SmallFont, fill=CardConstants.NameColor)

        return full_image
