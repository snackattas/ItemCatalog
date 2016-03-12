from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databaseSetup import User, Category, Item
from contextlib import contextmanager

engine = create_engine('sqlite:///itemCatalog.db')
DBSession = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = DBSession()
    try:
        yield session
    except:
        session.rollback()
        raise
    else:
        session.commit()

# Create 2 Users
with get_session() as session:
    User1 = User(name='Zach Attas Google',
                 email='zach.attas@gmail.com',
                 picture='https://upload.wikimedia.org/wikipedia/commons/4/4d/Cat_March_2010-1.jpg')
    User2 = User(name='Zach Attas Wesleyan',
                 email='zattas@wesleyan.edu',
                 picture='http://www.wesleyan.edu/communications/print_publications/style_guide/images/CardinalW_RC_BW.gif')
    session.add(User1)
    session.add(User2)

# Create some categories
with get_session() as session:
    restaurants = Category(
        name='Restaurants',
        user_id=1,
        picture='http://contentadmin.livebookings.com/dynamaster/image_archive/original/48f4c0dab33fa842baee08111521fca9.jpg')
    sports = Category(
        name='Sports',
        user_id=1,
        picture='http://mochadad.com/app/uploads/2012/12/sports.jpg')
    celebrities = Category(
        name='Celebrities',
        user_id=1,
        picture='https://pbs.twimg.com/profile_images/2029688967/Betty_Photo.jpg')
    singers = Category(
        name='Singers',
        user_id=1,
        picture='http://www.lookgreat-loseweight-savemoney.com/images/xJaylo1.jpg.pagespeed.ic.k_yutjwRq9.jpg')
    soups = Category(
        name='Soups',
        user_id=1,
        picture='http://images.clipartpanda.com/soup-clip-art-homemade-soup-clipart.jpg')
    bugs = Category(
        name='bugs',
        user_id=2,
        picture='http://worldartsme.com/images/cute-bug-clipart-1.jpg')
    sandwiches = Category(
        name='Sandwiches',
        user_id=2,
        picture='http://images.clipartpanda.com/sandwich-clipart-sandwich-half-3-md.png')
    holidays = Category(
        name='Holidays',
        user_id=2,
        picture='http://cnafinance.com/wp-content/uploads/2015/08/Bank-Holidays.jpg')
    countries = Category(
        name='Countries',
        user_id=2,
        picture='https://i.ytimg.com/vi/Gc8_t3PcafE/maxresdefault.jpg')
    mountains = Category(
        name='Mountains',
        user_id=2,
        picture='http://images.clipartpanda.com/mountain-clip-art-mountains_11.gif')

    session.add(restaurants)
    session.add(sports)
    session.add(celebrities)
    session.add(singers)
    session.add(soups)
    session.add(bugs)
    session.add(sandwiches)
    session.add(holidays)
    session.add(countries)
    session.add(mountains)

# Create some items for those categories
with get_session() as session:
    restaurant1 = Item(
        name='Giuseppos',
        description='Tama ai jo tupa ukki eika meri et jota ai. Ole osa lyoda kokka ole niita kohta litra. Jalessaan kay vai kun kasvoilla eli valtaansa varsinkin. Jai tavalla yha anastaa saa kuulkaa voi suoraan sylkisi. Ihmisilla he millainen ai majakoita semmoisen jo huonoista. Kaljamalla tuommoinen kaupunkiin moottoriin se te liikkeella muuhunkaan ja ei.',
        category_id=1,
        user_id=1,
        picture='http://grupoplascencia.com/img/logos/giuseppis.png')
    restaurant2 = Item(
        name='Peking Duck House',
        description='A famous duck dish from Beijing that has been prepared since the imperial era. The meat is prized for its thin, crisp skin, with authentic versions of the dish serving mostly the skin and little meat, sliced in front of the diners by the cook',
        category_id=1,
        user_id=1,
        picture='http://www.chinatownconnection.com/images/pekingducks.jpg')
    restaurant3 = Item(
        name='Super Stir Fry',
        description='Kodin tulen vetta osaan jos eli tuo sille menee kai. Katsoi monine tyhjan veisin on yhteen nahnyt se et. Ai kummitus jo ne mahdatte pyorahti et. Kun tullut voi tahdon kiilto jos vie. Jonkun niilla paljoa emanta nyt lahtea kun sitten luo tai. Jo kursailla tietenkin juoksette on ne istahtaen.',
        category_id=1,
        user_id=1,
        picture='https://pioneerwoman.files.wordpress.com/2015/10/dsc_4051.jpg')
    restaurant4 = Item(
        name='Ben and Jerrys',
        description='From a renovated gas station in Burlington, Vermont, to far-off places with names we sometimes mispronounce, the journey that began in 1978 with 2 guys and the ice cream business they built is as legendary as the ice cream is euphoric.',
        category_id=1,
        user_id=1,
        picture='https://upload.wikimedia.org/wikipedia/en/thumb/1/17/Ben_and_jerry_logo.svg/1024px-Ben_and_jerry_logo.svg.png')
    restaurant5 = Item(
        name='Applebees',
        description='It applebees',
        category_id=1,
        user_id=1,
        picture="http://traversemountain.alpineschools.org/wp-content/uploads/sites/51/2015/10/applebees-logo.jpg")
    restaurant6 = Item(
        name='Olive Garden',
        description='WHen here is fam',
        category_id=1,
        user_id=1,
        picture="http://media.olivegarden.com/images/site/logo.png")
    restaurant7 = Item(
        name='Chiles',
        description='the restaurant not the place ya dummy',
        category_id=1,
        user_id=1,
        picture="https://hilbersinc.com/wp-content/gallery/chilis-restaurant/img_6273a.jpg")
    restaurant8 = Item(
        name='Cheesecake Factory',
        description='super+fresh=delicious',
        category_id=1,
        user_id=1,
        picture="http://tomorrowproducts.com/wp-content/uploads/2016/02/cheesecake-factory-logo-chesecake-logo.jpg")
    restaurant9 = Item(
        name='Matched',
        description='super+fresh=delicious',
        category_id=1,
        user_id=1,
        picture="http://vignette3.wikia.nocookie.net/logopedia/images/7/72/Mcdonalds.jpg/revision/20140621181049")
    for n in range(1,10):
        restaurant = globals()['restaurant' + str(n)]
        session.add(restaurant)

# create some mountains with user 2
with get_session() as session:
    mountain1 = Item(
        name='Giuseppos',
        description='Tama ai jo tupa ukki eika meri et jota ai. Ole osa lyoda kokka ole niita kohta litra. Jalessaan kay vai kun kasvoilla eli valtaansa varsinkin. Jai tavalla yha anastaa saa kuulkaa voi suoraan sylkisi. Ihmisilla he millainen ai majakoita semmoisen jo huonoista. Kaljamalla tuommoinen kaupunkiin moottoriin se te liikkeella muuhunkaan ja ei.',
        category_id=1,
        user_id=2,
        picture='http://grupoplascencia.com/img/logos/giuseppis.png')
    mountain2 = Item(
        name='Peking Duck House',
        description='A famous duck dish from Beijing that has been prepared since the imperial era. The meat is prized for its thin, crisp skin, with authentic versions of the dish serving mostly the skin and little meat, sliced in front of the diners by the cook',
        category_id=1,
        user_id=2,
        picture='http://www.chinatownconnection.com/images/pekingducks.jpg')
    mountain3 = Item(
        name='Super Stir Fry',
        description='Kodin tulen vetta osaan jos eli tuo sille menee kai. Katsoi monine tyhjan veisin on yhteen nahnyt se et. Ai kummitus jo ne mahdatte pyorahti et. Kun tullut voi tahdon kiilto jos vie. Jonkun niilla paljoa emanta nyt lahtea kun sitten luo tai. Jo kursailla tietenkin juoksette on ne istahtaen.',
        category_id=1,
        user_id=2,
        picture='https://pioneerwoman.files.wordpress.com/2015/10/dsc_4051.jpg')
    mountain4 = Item(
        name='Ben and Jerrys',
        description='From a renovated gas station in Burlington, Vermont, to far-off places with names we sometimes mispronounce, the journey that began in 1978 with 2 guys and the ice cream business they built is as legendary as the ice cream is euphoric.',
        category_id=1,
        user_id=2,
        picture='https://upload.wikimedia.org/wikipedia/en/thumb/1/17/Ben_and_jerry_logo.svg/1024px-Ben_and_jerry_logo.svg.png')
    mountain5 = Item(
        name='Applebees',
        description='It applebees',
        category_id=1,
        user_id=2,
        picture="http://traversemountain.alpineschools.org/wp-content/uploads/sites/51/2015/10/applebees-logo.jpg")
    mountain6 = Item(
        name='Olive Garden',
        description='WHen here is fam',
        category_id=1,
        user_id=2,
        picture="http://media.olivegarden.com/images/site/logo.png")
    mountain7 = Item(
        name='Chiles',
        description='the restaurant not the place ya dummy',
        category_id=1,
        user_id=2,
        picture="https://hilbersinc.com/wp-content/gallery/chilis-restaurant/img_6273a.jpg")
    mountain8 = Item(
        name='Cheesecake Factory',
        description='super+fresh=delicious',
        category_id=1,
        user_id=2,
        picture="http://tomorrowproducts.com/wp-content/uploads/2016/02/cheesecake-factory-logo-chesecake-logo.jpg")
    mountain9 = Item(
        name='Matched',
        description='super+fresh=delicious',
        category_id=1,
        user_id=2,
        picture="http://vignette3.wikia.nocookie.net/logopedia/images/7/72/Mcdonalds.jpg/revision/20140621181049")
    for n in range(1,10):
        mountain = globals()['mountain' + str(n)]
        session.add(mountain)
