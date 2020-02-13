import pypyodbc
from random import randint


class MyriadCategory(object):
    id = None
    description = None

    def __init__(self, id=None, description=None):
        self.id = id
        self.description = description


class MyriadDBManager(object):
    conn = cur = None
    # XMAS | NUM1 | TOP10 | TWOYEARS | FIVEYEARS | 1970
    CATEGORY_NUM_ONE_TWO_YEARS = 0x010100
    CATEGORY_NUM_ONE_FIVE_YEARS = 0x010010
    CATEGORY_NUM_ONE_NINETEEN_SEVENTY = 0x010001
    CATEGORY_TOP_TEN_TWO_YEARS = 0x001100
    CATEGORY_TOP_TEN_FIVE_YEARS = 0x001010
    CATEGORY_TOP_TEN_NINETEEN_SEVENTY = 0x001001
    CATEGORY_CHRISTMAS = 0x100000
    CATEGORY_OTHER = 0x000000

    categories = {
        CATEGORY_NUM_ONE_TWO_YEARS: MyriadCategory(
            description="NumOneTwoYears"),
        CATEGORY_NUM_ONE_FIVE_YEARS: MyriadCategory(
            description="NumOneFiveYears"),
        CATEGORY_NUM_ONE_NINETEEN_SEVENTY: MyriadCategory(
            description="NumOneSince1970"),

        CATEGORY_TOP_TEN_TWO_YEARS: MyriadCategory(
            description="TopTenTwoYears"),
        CATEGORY_TOP_TEN_FIVE_YEARS: MyriadCategory(
            description="TopTenFiveYears"),
        CATEGORY_TOP_TEN_NINETEEN_SEVENTY: MyriadCategory(
            description="TopTenSince1970"),

        CATEGORY_CHRISTMAS: MyriadCategory(description="Christmas"),
        CATEGORY_OTHER: MyriadCategory(description="Other Music")
    }

    def __init__(self, db_path):
        drv = [x for x in pypyodbc.drivers() if x.startswith(
            'Microsoft Access Driver')]
        connection_string = 'Driver={};DBQ={}'.format(drv[0], db_path)
        self.conn = pypyodbc.connect(connection_string, ansi=True)
        self.cur = self.conn.cursor()

        self.setupCategoryIds()

    def getSongList(self):
        sql = 'SELECT MusicTitle,Performer,GUID FROM Songs WHERE NOT Category=? ORDER BY OriginallyAddedDate DESC'
        self.cur.execute(
            sql, [self.categories[self.CATEGORY_OTHER].id])
        rows = self.cur.fetchall()

        data = [{'title': row[0], 'artist':row[1], 'id':row[2]}
                for row in rows]
        return data

    def setupCategoryIds(self):

        # Try to find the categories with the existing descriptions in the DB
        for cat in self.categories.iteritems():
            sql = "SELECT ItemNumber FROM SongCategories WHERE Description=?"
            self.cur.execute(sql, [cat[1].description])
            row = self.cur.fetchone()

            if row:
                self.categories[cat[0]].id = row[0]

            else:
                print "No category name with {} found! Creating...".format(
                    cat[1].description)
                created_id = self.createCategory(cat[1].description)
                if created_id:
                    self.categories[cat[0]].id = created_id
                else:
                    pass

        # self

    def createCategory(self, category_desc):
        sql = "INSERT INTO SongCategories (ItemNumber, Description,BackColour) VALUES (?,?,?)"

        id_to_create = 0
        for i in xrange(1, 1000):
            id_num_sql = "SELECT * FROM SongCategories WHERE ItemNumber=?"
            self.cur.execute(id_num_sql, [i])
            results = self.cur.fetchall()
            if len(results) == 0:
                id_to_create = i
                break

        try:
            # 16777215 is the decimal representation of the max hex colour value #FFFFFF
            # So we're picking a random colour
            self.cur.execute(
                sql, [id_to_create, category_desc, randint(0, 16777215)])
            self.cur.commit()
        except Exception as e:
            print "Could not create category {} - {}".format(
                category_desc, e.message)
            self.cur.rollback()

        return id_to_create

    def setSongCategory(self, song_id, category_id):
        sql = "UPDATE Songs SET Category=? WHERE GUID=?"
        try:
            self.cur.execute(sql, [category_id, song_id])
            self.cur.commit()
        except Exception as e:
            print "Could not update song with ID {} to Category {}: {}".format(
                song_id,  category_id, e)
