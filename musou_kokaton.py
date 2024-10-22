import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm



class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    state = "normal" #演習問題4
    hyper_life = 0

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if Bird.state == "hyper": # 演習問題4
            self.image = pg.transform.laplacian(self.image)
            Bird.hyper_life -= 1
        if Bird.hyper_life < 0:
            Bird.state = "normal"

        screen.blit(self.image, self.rect)
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6



    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0 = 0):
        """
        ビーム画像Surfaceを生成する
        引数1 bird：ビームを放つこうかとん
        引数2 angle0：ビームの回転角度(初期値 = 0)
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle + angle0, 2.0)
        self.vx = math.cos(math.radians(angle + angle0))
        self.vy = -math.sin(math.radians(angle + angle0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam(pg.sprite.Sprite):
    """
    複数ビームに関するビーム
    """
    
    def __init__(self, bird: pg.Surface, num: int):
        """
        複数のビーム画像Surfaceを生成する
        引数1 bird：ビームを放つこうかとん
        引数2 num：ビームの数
        """
        
        super().__init__() 
        self.bird = bird
        self.num = num
        
    def gen_beams(self):
        """
        複数のBeamインスタンスを生成
        """
        beam_lst=[]
        dire_lst = list(range(-50, 51, int(100 / (self.num - 1))))
        for i in dire_lst:
            beam_lst.append(Beam(self.bird, i))
        return beam_lst
    
    
class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)
        

        # 爆弾を投下しない状態をチェック
        if self.interval == float('inf'):
            return

#実装2
class Gravity(pg.sprite.Sprite):
    def __init__(self,life=400):
        super().__init__()
        self.image = pg.Surface((WIDTH,HEIGHT))
        self.image.fill((0,0,0))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class EMP:
    """
    電磁パルス（EMP）に関するクラス
    """
    def __init__(self, enemies: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        """
        EMPを発動させ、敵機と爆弾を無効化する
        引数1 enemies：Enemyインスタンスのグループ
        引数2 bombs：Bombインスタンスのグループ
        引数3 screen：画面Surface
        """
        # 敵機の無効化
        for emy in enemies:
            emy.interval = float('inf')  # 無限大に設定し、爆弾を投下できなくする
            emy.image = pg.transform.laplacian(emy.image)  # ラプラシアンフィルタを適用
            emy.image.set_colorkey((0,0,0))
        # 爆弾の無効化
        for bomb in bombs:
            bomb.speed /= 2  # スピードを半減させる
            bomb.state = "inactive"  # 爆発しない状態にする
            
        
        # EMP効果の視覚的演出（0.05秒間、画面に黄色い矩形を表示）
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)  # 透明度を設定
        overlay.fill((255, 255, 0))  # 黄色に設定
        screen.blit(overlay, (0, 0))
        pg.display.update()
        time.sleep(0.05)  # 0.05秒表示

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    gravity = None

    bird = Bird(3, (900, 400))
    neobeam = NeoBeam(bird, 8)
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()

    gravity = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if key_lst[pg.K_SPACE]: # 入力判定
                if key_lst[pg.K_LSHIFT]:
                  beams.add(neobeam.gen_beams())
                else:
                  beams.add(Beam(bird))
        screen.blit(bg_img, [0, 0])

        if key_lst[pg.K_RSHIFT] and (score.value >= 10): # 演習問題4
            score.value -= 100
            Bird.state = "hyper"
            Bird.hyper_life = 500

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        # EMP発動条件：スコアが20以上かつ「e」キーが押された場合
        if key_lst[pg.K_e] and score.value >= 20:
            EMP(emys, bombs, screen)  # EMP発動
            score.value -= 20  # スコアから20を引く

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        check = pg.sprite.spritecollide(bird, bombs, True) # 演習問題4
        if len(check) != 0:
            if Bird.state == "hyper":
                score.value += 1
                for bomb in check:
                    exps.add(Explosion(bomb, 50))
            else:
                if len(check) != 0: 
                    bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return
        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        #実装2
        if key_lst[pg.K_RETURN] and score.value >= 0:
            if not gravity:
                gravity.add(Gravity(400))
                score.value -= 200
            
        for bomb in pg.sprite.groupcollide(bombs,gravity,True,False).keys():
            exps.add(Explosion(bomb,50))
            score.value += 1

        for emy in pg.sprite.groupcollide(emys,gravity,True,False).keys():
            exps.add(Explosion(emy,100))
            score.value += 1

            bird.change_img(6,screen)


        gravity.draw(screen)
        gravity.update()
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()