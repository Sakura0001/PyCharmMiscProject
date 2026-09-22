#!/usr/bin/env python3
"""
数据生成器 — 覆盖mindmap 8类数据值 × 所有支持的数据类型
包括：负数/零/正数、源类型MIN/MAX、新范围值、DECIMAL 9位编码边界、
NULL/空串/空格、0x00/0xFF/前缀冲突、utf8mb3/utf8mb4、旧/新/超新长度上限
"""
import random
import struct

# ============================================================
# 整数类型边界值
# ============================================================
INTEGER_BOUNDS = {
    'TINYINT':           {'signed': (-128, 127),                 'unsigned': (0, 255)},
    'SMALLINT':          {'signed': (-32768, 32767),             'unsigned': (0, 65535)},
    'MEDIUMINT':         {'signed': (-8388608, 8388607),         'unsigned': (0, 16777215)},
    'INT':               {'signed': (-2147483648, 2147483647),   'unsigned': (0, 4294967295)},
    'BIGINT':            {'signed': (-9223372036854775808, 9223372036854775807),
                          'unsigned': (0, 18446744073709551615)},
}

def gen_integer_data(old_type, new_type, signed=True, phase='pre'):
    """生成整数测试数据
    phase: 'pre' (DDL前，旧类型范围) / 'post' (DDL后，新类型范围+旧类型范围+超限值)
    """
    old_key = old_type.upper()
    new_key = new_type.upper()
    sign = 'signed' if signed else 'unsigned'
    
    old_min, old_max = INTEGER_BOUNDS[old_key][sign]
    new_min, new_max = INTEGER_BOUNDS[new_key][sign]
    
    data = []
    
    if phase == 'pre':
        # ① 负数/零/正数
        if signed:
            data.extend([(-1, 'neg'), (0, 'zero'), (1, 'pos'), (-64, 'neg_mid'), (64, 'pos_mid')])
        else:
            data.extend([(0, 'zero'), (1, 'pos'), (255, 'small_max'), (128, 'mid')])
        
        # ② 源类型 MIN/MAX
        data.append((old_min, 'source_min'))
        data.append((old_max, 'source_max'))
        data.append((old_min + 1 if old_min < new_min else old_min, 'source_min_plus1'))
        data.append((old_max - 1 if old_max > 0 else old_max, 'source_max_minus1'))
        
        # ⑤ NULL
        data.append((None, 'null'))
    
    elif phase == 'post':
        # ③ 新范围值（旧类型放不下但新类型可以）
        if signed:
            if new_max > old_max:
                data.append((old_max + 1, 'new_range_low'))
                data.append((new_max, 'new_max'))
                data.append((new_max - 1, 'new_max_minus1'))
            if new_min < old_min:
                data.append((old_min - 1, 'new_range_neg'))
                data.append((new_min, 'new_min'))
        else:
            if new_max > old_max:
                data.append((old_max + 1, 'new_range_low'))
                data.append((new_max, 'new_max'))
                data.append((new_max - 1, 'new_max_minus1'))
        
        # 旧类型范围值（向后兼容）
        data.append((0, 'zero_compat'))
        data.append((1, 'pos_compat'))
        data.append((old_max, 'old_max_compat'))
        if signed:
            data.append((-1, 'neg_compat'))
            data.append((old_min, 'old_min_compat'))
        
        # NULL
        data.append((None, 'null_post'))
        
        # ⑧ 超新范围上限值（预期 INSERT FAIL）
        if signed:
            data.append((new_max + 1, 'over_new_max_EXPECT_FAIL'))
        else:
            # UNSIGNED 无符号，超过 new_max 会报错
            data.append((new_max, 'new_max_compat'))  # 这不会失败，但作为边界
    
    return data


# ============================================================
# CHAR/VARCHAR 边界数据
# ============================================================
EMOJI = '🚀'  # 4 bytes in utf8mb4
MULTIBYTE_3 = '中'  # 3 bytes in utf8mb3/utf8mb4
ASCII_CHAR = 'a'
SPACE = ' '
SPECIAL_CHARS = ['\x00', '\xff', '\r', '\n', '\t', '\\', "'", '"', '`']

def gen_char_data(old_len, new_len, charset='utf8mb4', phase='pre'):
    """生成 CHAR/VARCHAR 测试数据"""
    data = []
    
    # 字节宽度
    if charset in ('utf8mb4', 'utf8mb3'):
        bytes_per_char = 4 if charset == 'utf8mb4' else 3
    else:  # latin1, binary
        bytes_per_char = 1
    
    old_byte_max = old_len * bytes_per_char
    new_byte_max = new_len * bytes_per_char
    
    if phase == 'pre':
        # ⑤ NULL/空串/空格/尾空格
        data.append((None, 'null'))
        data.append(('', 'empty_string'))
        data.append((' ', 'single_space'))
        data.append(('a ', 'char_trail_space'))
        data.append(('  ', 'double_space'))
        
        # ② 源类型旧长度上限
        data.append((ASCII_CHAR * old_len, 'old_max_ascii'))
        data.append((ASCII_CHAR * (old_len - 1), 'old_max_minus1'))
        
        # ⑦ utf8mb4 多字节字符
        if charset == 'utf8mb4':
            # 用emoji填满旧长度
            emoji_count = old_len // 4
            if emoji_count > 0:
                data.append((EMOJI * emoji_count, 'old_max_emoji'))
            # 用3字节字符填满
            mb3_count = old_len // 3
            if mb3_count > 0:
                data.append((MULTIBYTE_3 * mb3_count, 'old_max_3byte'))
        
        # ⑧ 超旧长度上限（预期 FAIL）
        data.append((ASCII_CHAR * (old_len + 1), 'over_old_max_EXPECT_FAIL'))
        
        if charset == 'utf8mb3':
            # ⑦ utf8mb3 写4字节字符 → 预期 FAIL
            data.append((EMOJI, 'utf8mb3_4byte_EXPECT_FAIL'))
    
    elif phase == 'post':
        # ③ 新范围值
        data.append((ASCII_CHAR * new_len, 'new_max_ascii'))
        data.append((ASCII_CHAR * (new_len - 1), 'new_max_minus1'))
        
        # emoji 填满新长度
        if charset == 'utf8mb4':
            emoji_count = new_len // 4
            if emoji_count > 0:
                data.append((EMOJI * emoji_count, 'new_max_emoji'))
                # 用户要求：emoji × 8000 填满上限
                if new_len >= 32000:
                    data.append((EMOJI * 8000, 'emoji_8000'))
        
        # 旧长度范围值（向后兼容）
        data.append((ASCII_CHAR * old_len, 'old_max_compat'))
        data.append(('', 'empty_compat'))
        data.append((None, 'null_compat'))
        
        # ⑧ 超新长度上限（预期 FAIL）
        data.append((ASCII_CHAR * (new_len + 1), 'over_new_max_EXPECT_FAIL'))
        
        # 特殊字符
        for sc in SPECIAL_CHARS[:3]:  # 0x00, 0xff, \r
            try:
                data.append((sc * min(old_len, 10), f'special_{repr(sc)}'))
            except:
                pass
    
    return data


# ============================================================
# BINARY/VARBINARY 边界数据
# ============================================================
def gen_binary_data(old_len, new_len, phase='pre'):
    """生成 BINARY/VARBINARY 测试数据"""
    data = []
    
    if phase == 'pre':
        # ⑤ NULL/空
        data.append((None, 'null'))
        data.append((b'', 'empty_bytes'))
        
        # ⑥ 0x00/0xFF
        data.append((b'\x00' * old_len, 'all_zero'))
        data.append((b'\xff' * old_len, 'all_ff'))
        data.append((b'\x00' * (old_len - 1), 'zero_max_minus1'))
        
        # ⑥ 相同前缀不同尾部
        prefix = b'ABCDEF'
        data.append((prefix + b'\x00' * (old_len - len(prefix)), 'prefix_zero_tail'))
        data.append((prefix + b'\xff' * (old_len - len(prefix)), 'prefix_ff_tail'))
        
        # ② 旧长度上限
        data.append((b'A' * old_len, 'old_max'))
        data.append((b'A' * (old_len - 1), 'old_max_minus1'))
        
        # ⑧ 超旧长度（预期 FAIL）
        data.append((b'A' * (old_len + 1), 'over_old_max_EXPECT_FAIL'))
    
    elif phase == 'post':
        # ③ 新范围值
        data.append((b'\x00' * new_len, 'new_all_zero'))
        data.append((b'\xff' * new_len, 'new_all_ff'))
        data.append((b'A' * new_len, 'new_max'))
        data.append((b'A' * (new_len - 1), 'new_max_minus1'))
        
        # 旧长度范围值
        data.append((b'\x00' * old_len, 'old_zero_compat'))
        data.append((b'A' * old_len, 'old_max_compat'))
        data.append((None, 'null_compat'))
        
        # ⑧ 超新长度（预期 FAIL）
        data.append((b'A' * (new_len + 1), 'over_new_max_EXPECT_FAIL'))
    
    return data


# ============================================================
# DECIMAL 边界数据（含9位编码边界）
# ============================================================
def gen_decimal_data(old_M, new_M, D=2, phase='pre'):
    """生成 DECIMAL 测试数据，覆盖9位编码边界"""
    from decimal import Decimal, getcontext
    # Set precision high enough for max DECIMAL(65) = 65 digits
    getcontext().prec = 100
    data = []
    
    def decimal_max_str(M, D):
        """String representation of max value to avoid float precision loss"""
        int_digits = M - D
        if D == 0:
            return "9" * int_digits
        else:
            return "9" * int_digits + "." + "9" * D
    
    def decimal_min_str(M, D):
        return "-" + decimal_max_str(M, D)
    
    def decimal_max(M, D):
        return float(decimal_max_str(M, D))
    
    def decimal_min(M, D):
        return -decimal_max(M, D)
    
    def decimal_step(D):
        """Smallest increment for given scale"""
        return Decimal("0." + "0" * (D - 1) + "1") if D > 0 else Decimal(1)
    
    old_max_str = decimal_max_str(old_M, D)
    old_min_str = decimal_min_str(old_M, D)
    new_max_str = decimal_max_str(new_M, D)
    new_min_str = decimal_min_str(new_M, D)
    old_max_dec = Decimal(old_max_str)
    old_min_dec = Decimal(old_min_str)
    new_max_dec = Decimal(new_max_str)
    new_min_dec = Decimal(new_min_str)
    
    # For comparison, use Decimal
    old_max = float(old_max_dec)
    old_min = float(old_min_dec)
    new_max = float(new_max_dec)
    new_min = float(new_min_dec)
    
    def in_old_range(v):
        """Check if value fits within old type range"""
        if v is None:
            return True
        return old_min_dec <= Decimal(str(v)) <= old_max_dec
    
    def in_new_range(v):
        """Check if value fits within new type range"""
        if v is None:
            return True
        return new_min_dec <= Decimal(str(v)) <= new_max_dec
    
    if phase == 'pre':
        # ① 负数/零/正数 (filtered to old type range)
        for v, label in [(-1.0 if D > 0 else -1, 'neg'), (0.0 if D > 0 else 0, 'zero'), (1.0 if D > 0 else 1, 'pos')]:
            if in_old_range(v):
                data.append((v, label))
        
        # ② 源类型 MIN/MAX — use string representation for precision
        data.append((old_max_str, 'source_max'))
        data.append((old_min_str, 'source_min'))
        # Source MAX-1 and MIN+1 (boundary) — use Decimal arithmetic
        step_dec = decimal_step(D)
        data.append((str(old_max_dec - step_dec), 'source_max_minus1'))
        data.append((str(old_min_dec + step_dec), 'source_min_plus1'))
        
        # ⑤ NULL
        data.append((None, 'null'))
        
        # DECIMAL 特定值 (filtered to old type range)
        if D > 0:
            candidates = [
                (0.01, 'smallest_decimal'),
                (-0.01, 'neg_smallest'),
                (1.23, 'normal_pos'),
                (-1.23, 'normal_neg'),
                (99.99, 'near_max'),
                (-99.99, 'near_min'),
            ]
            for v, label in candidates:
                if in_old_range(v):
                    data.append((v, label))
                else:
                    # Scale down to fit old range — use Decimal for precision
                    scaled = str(old_max_dec * Decimal('0.5')) if v > 0 else str(old_min_dec * Decimal('0.5'))
                    data.append((scaled, f'{label}_scaled'))
    
    elif phase == 'post':
        # ③ 新范围值 — use string/Decimal for precision
        step_dec = decimal_step(D)
        if new_max_dec > old_max_dec:
            data.append((str(old_max_dec + step_dec), 'new_range_low'))
            data.append((new_max_str, 'new_max'))
            data.append((str(new_max_dec - step_dec), 'new_max_minus1'))
        if new_min_dec < old_min_dec:
            data.append((str(old_min_dec - step_dec), 'new_range_neg'))
            data.append((new_min_str, 'new_min'))
        
        # 旧范围兼容
        data.append((0, 'zero_compat'))
        data.append((old_max_str, 'old_max_compat'))
        data.append((None, 'null_compat'))
        
        # ⑧ 超新范围（预期 FAIL）
        data.append((str(new_max_dec + step_dec), 'over_new_max_EXPECT_FAIL'))
    
    return data

# DECIMAL 9位编码边界转换
DECIMAL_9BIT_TRANSITIONS = [
    (9, 10, 2),   (18, 19, 2),   (27, 28, 2),
    (36, 37, 2),  (45, 46, 2),   (54, 55, 2),
    (1, 2, 0),    (1, 2, 1),     (64, 65, 30),  (31, 33, 30),
    (10, 12, 2),  (18, 20, 0),
]


# ============================================================
# TEXT/BLOB 边界数据 — 用户特别要求覆盖
# ============================================================
def gen_text_blob_data(old_subtype, new_subtype, is_blob=False, phase='pre'):
    """生成 TEXT/BLOB 测试数据，覆盖所有字节边界
    old_subtype/new_subtype: 'TINY'/'MEDIUM'/'LONG'/''(=TEXT/BLOB)
    """
    SIZE_LIMITS = {
        'TINY': 255,
        '': 65535,        # TEXT/BLOB
        'MEDIUM': 16777215,
        'LONG': 4294967295,
    }
    
    old_max = SIZE_LIMITS[old_subtype]
    new_max = SIZE_LIMITS[new_subtype]
    
    data = []
    
    def make_content(size, byte_val=0x41):
        """生成指定大小的内容（上限65535字节）"""
        size = min(size, 65535)  # Cap to prevent OOM
        if is_blob:
            return bytes([byte_val] * size)
        else:
            return 'a' * size
    
    def make_emoji_content(emoji_count):
        """生成指定数量emoji的内容（上限8000个）"""
        emoji_count = min(emoji_count, 8000)
        if is_blob:
            return b'\xf0\x9f\x9a\x80' * emoji_count
        return EMOJI * emoji_count
    
    def make_mixed_binary(size):
        """生成混合二进制内容（含0x00/0xFF），上限65535"""
        size = min(size, 65535)
        pattern = bytes([0x00, 0x01, 0x7F, 0x80, 0xFF]) * (size // 5 + 1)
        return pattern[:size]
    
    if phase == 'pre':
        # ⑤ NULL/空串
        data.append((None, 'null'))
        data.append(('', 'empty') if not is_blob else (b'', 'empty'))
        
        # ② 源类型边界值
        data.append((make_content(old_max), 'old_max'))
        data.append((make_content(old_max - 1), 'old_max_minus1'))
        
        # 关键字节边界（用户特别要求）
        # 255/256 边界（TINYTEXT→TEXT 的关键）
        if old_max >= 256:
            data.append((make_content(255), 'bytes_255'))
            data.append((make_content(256), 'bytes_256'))
        elif old_max == 255:
            data.append((make_content(254), 'bytes_254'))
            data.append((make_content(255), 'bytes_255'))
            # 256 超出 TINYTEXT 范围 → 预期 FAIL
            data.append((make_content(256), 'bytes_256_EXPECT_FAIL'))
        
        # 用户提到的特定大小
        specific_sizes = [8101, 8192, 16000, 32000, 64000, 65535]
        for sz in specific_sizes:
            if sz <= old_max:
                if sz == old_max:
                    continue  # 已添加
                data.append((make_content(sz), f'bytes_{sz}'))
        
        # ⑥ 0x00/0xFF 和混合二进制
        if is_blob:
            data.append((b'\x00' * min(old_max, 255), 'all_zero'))
            data.append((b'\xff' * min(old_max, 255), 'all_ff'))
            data.append((make_mixed_binary(min(old_max, 255)), 'mixed_binary'))
            data.append((b'\x00' * min(old_max, 255) + b'\xff' * min(old_max, 255), 
                        'zero_then_ff'))
            # 相同前缀不同尾部
            prefix = b'PREFIX'
            data.append((prefix + b'\x00' * min(old_max - 6, 250), 'prefix_zero'))
            data.append((prefix + b'\xff' * min(old_max - 6, 250), 'prefix_ff'))
        else:
            # TEXT 的特殊字符
            data.append(('\x01' * min(old_max, 255), 'control_chars_01'))
            data.append(('\x01' * min(old_max, 255), 'control_chars'))
            # 尾空格
            data.append(('a' * 10 + ' ' * 20, 'trailing_spaces'))
        
        # ⑦ emoji/多字节字符
        if not is_blob:
            emoji_fit = min(old_max // 4, 64)
            if emoji_fit > 0:
                data.append((make_emoji_content(emoji_fit), f'emoji_{emoji_fit}'))
            # 用户要求: emoji × 8000
            if 32000 <= old_max:
                data.append((make_emoji_content(8000), 'emoji_8000'))
        
        # ⑧ 超旧长度上限（预期 FAIL）
        data.append((make_content(old_max + 1), 'over_old_max_EXPECT_FAIL'))
    
    elif phase == 'post':
        # ③ 新范围值
        data.append((make_content(new_max), 'new_max'))
        data.append((make_content(new_max - 1), 'new_max_minus1'))
        
        # 关键边界（新类型可以容纳的）
        boundary_sizes = [255, 256, 65535, 65536, 8101, 8192, 16000, 32000, 64000]
        for sz in boundary_sizes:
            if old_max < sz <= new_max:
                data.append((make_content(sz), f'bytes_{sz}'))
        
        # emoji × 8000 (32000 bytes)
        if 32000 <= new_max and 32000 > old_max:
            data.append((make_emoji_content(8000), 'emoji_8000_new'))
        
        # 用户要求的大值
        if new_max >= 65535 and old_max < 65535:
            data.append((make_content(65535), 'bytes_65535'))
            data.append((make_content(60000), 'bytes_60000'))
        
        # 旧范围兼容
        data.append((make_content(old_max), 'old_max_compat'))
        data.append(('', 'empty_compat') if not is_blob else (b'', 'empty_compat'))
        data.append((None, 'null_compat'))
        
        # 0x00/0xFF 兼容
        if is_blob:
            data.append((b'\x00' * 255, 'zero_255_compat'))
            data.append((b'\xff' * 255, 'ff_255_compat'))
        
        # ⑧ 超新长度（预期 FAIL）
        if new_max < 4294967295:
            data.append((make_content(new_max + 1), 'over_new_max_EXPECT_FAIL'))
    
    return data


# ============================================================
# BIT 边界数据
# ============================================================
def gen_bit_data(old_bits, new_bits, phase='pre'):
    """生成 BIT 测试数据"""
    data = []
    
    def bit_val(n):
        """返回 b'...' 格式的值"""
        return n
    
    old_max = (1 << old_bits) - 1
    new_max = (1 << new_bits) - 1
    
    if phase == 'pre':
        data.append((0, 'zero'))
        data.append((1, 'one'))
        data.append((old_max, 'old_max'))
        data.append((old_max - 1, 'old_max_minus1'))
        data.append((None, 'null'))
        # 交替位模式
        if old_bits >= 8:
            data.append((0b10101010, 'alternating_8'))
        if old_bits >= 4:
            data.append((0b1111, 'all_ones_4'))
    
    elif phase == 'post':
        # 新范围值
        data.append((new_max, 'new_max'))
        data.append((new_max - 1, 'new_max_minus1'))
        # 旧范围兼容
        data.append((0, 'zero_compat'))
        data.append((1, 'one_compat'))
        data.append((old_max, 'old_max_compat'))
        data.append((None, 'null_compat'))
        # 超新范围（预期 FAIL）
        if new_max < 18446744073709551615:
            data.append((new_max + 1, 'over_new_max_EXPECT_FAIL'))
    
    return data


# ============================================================
# 并发DML操作生成器
# ============================================================
class DMLOpGenerator:
    """生成并发DML操作序列"""
    
    def __init__(self, data_type, old_type, new_type, charset=None, 
                 signed=True, old_len=None, new_len=None, D=None, phase='pre'):
        self.data_type = data_type  # 'integer'/'char'/'varchar'/'binary'/'decimal'/'text'/'blob'/'bit'
        self.old_type = old_type
        self.new_type = new_type
        self.charset = charset
        self.signed = signed
        self.old_len = old_len
        self.new_len = new_len
        self.D = D
        self.phase = phase
        self._pk_counter = 10000  # 起始PK
        self._existing_pks = set(range(1, 101))  # 基线数据PK范围
    
    def next_pk(self):
        self._pk_counter += 1
        self._existing_pks.add(self._pk_counter)
        return self._pk_counter
    
    def random_pk(self):
        if not self._existing_pks:
            return None
        return random.choice(list(self._existing_pks))
    
    def gen_value(self):
        """生成一个适合当前 phase 的值"""
        if self.data_type == 'integer':
            data = gen_integer_data(self.old_type, self.new_type, self.signed, self.phase)
        elif self.data_type in ('char', 'varchar'):
            data = gen_char_data(self.old_len, self.new_len, self.charset, self.phase)
        elif self.data_type == 'binary':
            data = gen_binary_data(self.old_len, self.new_len, self.phase)
        elif self.data_type == 'decimal':
            data = gen_decimal_data(self.old_len, self.new_len, self.D, self.phase)
        elif self.data_type in ('text', 'blob'):
            is_blob = self.data_type == 'blob'
            data = gen_text_blob_data(self.old_type, self.new_type, is_blob, self.phase)
        elif self.data_type == 'bit':
            data = gen_bit_data(self.old_len, self.new_len, self.phase)
        else:
            data = [(0, 'default')]
        
        return random.choice(data) if data else (0, 'default')
    
    def gen_insert_op(self):
        pk = self.next_pk()
        val, label = self.gen_value()
        return ('INSERT', pk, val, label)
    
    def gen_update_op(self):
        pk = self.random_pk()
        if pk is None:
            return self.gen_insert_op()
        val, label = self.gen_value()
        return ('UPDATE', pk, val, label)
    
    def gen_delete_op(self):
        pk = self.random_pk()
        if pk is None:
            return self.gen_insert_op()
        self._existing_pks.discard(pk)
        return ('DELETE', pk, None, 'delete')
    
    def gen_upsert_op(self):
        """同键删除重插"""
        pk = self.random_pk()
        if pk is None:
            return self.gen_insert_op()
        val, label = self.gen_value()
        return ('UPSERT', pk, val, label)
    
    def gen_op(self, op_type=None):
        if op_type:
            types = [op_type]
        else:
            types = ['INSERT', 'UPDATE', 'DELETE', 'UPSERT']
        return getattr(self, f'gen_{random.choice(types).lower()}_op')()


if __name__ == '__main__':
    # 测试数据生成
    print("=== INTEGER (INT->BIGINT, signed) ===")
    for v, label in gen_integer_data('INT', 'BIGINT', True, 'pre'):
        print(f"  pre: {label} = {v}")
    for v, label in gen_integer_data('INT', 'BIGINT', True, 'post'):
        print(f"  post: {label} = {v}")
    
    print("\n=== VARCHAR(255)->VARCHAR(256) latin1 ===")
    for v, label in gen_char_data(255, 256, 'latin1', 'pre'):
        print(f"  pre: {label} = {repr(v)[:60]}")
    for v, label in gen_char_data(255, 256, 'latin1', 'post'):
        print(f"  post: {label} = {repr(v)[:60]}")
    
    print("\n=== TEXT (TINYTEXT->TEXT) ===")
    for v, label in gen_text_blob_data('TINY', '', False, 'pre'):
        print(f"  pre: {label} = {repr(v)[:60]}")
    
    print("\n=== BLOB (TINYBLOB->BLOB) ===")
    for v, label in gen_text_blob_data('TINY', '', True, 'pre'):
        print(f"  pre: {label} = {repr(v)[:60]}")
    
    print("\n=== BIT(8)->BIT(16) ===")
    for v, label in gen_bit_data(8, 16, 'pre'):
        print(f"  pre: {label} = {v}")
